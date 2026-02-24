"""
Filesystem-based SenateDataSource for Valet.
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from .types import Senator, VoteEvent
from .errors import SenateDataUnavailableError, SenateDataValidationError

class SenateDataSource:
    def _ensure_init(self):
        if not self._initialized:
            self._init()
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or os.environ.get("SENATE_DATA_DIR")
        self._initialized = False
        self._senators_by_id: Dict[str, Senator] = {}
        self._senators_by_name: List[Senator] = []
        self._votes_by_senator_id: Dict[str, List[VoteEvent]] = {}
        self._votes_by_bill_and_senator: Dict[str, VoteEvent] = {}

    def _init(self):
        if self._initialized:
            return
        if not self.data_dir:
            raise SenateDataUnavailableError("SENATE_DATA_DIR is not set.")
        root = Path(self.data_dir)
        events_dir = root / "events"
        senators_dir = root / "senators"
        if not (root.exists() and events_dir.exists() and senators_dir.exists()):
            raise SenateDataUnavailableError(f"Missing required Senate data directories under {self.data_dir}")
        # Optional manifest.json validation
        manifest = root / "manifest.json"
        if manifest.exists():
            with open(manifest, encoding="utf-8") as f:
                try:
                    manifest_data = json.load(f)
                    if "schema_version" not in manifest_data:
                        raise SenateDataValidationError("manifest.json missing schema_version")
                except Exception as e:
                    raise SenateDataValidationError(f"Invalid manifest.json: {e}")
        # Load senators
        for file in senators_dir.glob("*.json"):
            with open(file, encoding="utf-8") as f:
                try:
                    senator = json.load(f)
                    if not senator.get("id") or not senator.get("name"):
                        raise SenateDataValidationError(f"Senator missing id or name in {file}")
                    self._senators_by_id[senator["id"]] = senator
                    self._senators_by_name.append(senator)
                except Exception as e:
                    raise SenateDataValidationError(f"Invalid senator record in {file}: {e}")
        # Load vote events
        for file in events_dir.glob("*.json"):
            with open(file, encoding="utf-8") as f:
                try:
                    event = json.load(f)
                    if not (event.get("event_id") and event.get("senator_id") and event.get("bill_id") and event.get("vote")):
                        raise SenateDataValidationError(f"VoteEvent missing required fields in {file}")
                    event["source_file"] = str(file.relative_to(root))
                    self._votes_by_senator_id.setdefault(event["senator_id"], []).append(event)
                    key = f"{event['bill_id']}:{event['senator_id']}"
                    self._votes_by_bill_and_senator[key] = event
                except Exception as e:
                    raise SenateDataValidationError(f"Invalid vote event in {file}: {e}")
        self._initialized = True

    def getSenatorById(self, senator_id: str) -> Optional[Senator]:
        self._ensure_init()
        return self._senators_by_id.get(senator_id)

    def searchSenators(self, query: str) -> List[Senator]:
        self._ensure_init()
        q = query.lower()
        return [s for s in self._senators_by_name if q in s["name"].lower()]

    def getVotesBySenator(self, senator_id: str, start: Optional[str] = None, end: Optional[str] = None) -> List[VoteEvent]:
        self._ensure_init()
        votes = self._votes_by_senator_id.get(senator_id, [])
        # Optionally filter by timestamp
        if start or end:
            def in_range(ev):
                ts = ev.get("timestamp")
                if not ts:
                    return False
                if start and ts < start:
                    return False
                if end and ts > end:
                    return False
                return True
            votes = [v for v in votes if in_range(v)]
        return votes

    def getVoteByBillAndSenator(self, bill_id: str, senator_id: str) -> Optional[VoteEvent]:
        self._ensure_init()
        return self._votes_by_bill_and_senator.get(f"{bill_id}:{senator_id}")

    def listSenators(self) -> List[Senator]:
        """Return all loaded senators."""
        self._ensure_init()
        return list(self._senators_by_name)
