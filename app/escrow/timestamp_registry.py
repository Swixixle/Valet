from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class TimestampEntry:
    hash: str
    ipfs_cid: str
    timestamp: str  # ISO-8601 UTC


def create_entry(content_hash: str, ipfs_cid: str) -> TimestampEntry:
    """Create a new TimestampEntry with the current UTC timestamp."""
    ts = datetime.now(tz=UTC).isoformat()
    return TimestampEntry(hash=content_hash, ipfs_cid=ipfs_cid, timestamp=ts)


def append_to_ledger(entry: TimestampEntry, ledger_path: Path) -> None:
    """Append *entry* to the local JSON-lines ledger at *ledger_path*.

    Creates the file if it does not exist.  Each line is a JSON object.
    """
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry)) + "\n")
