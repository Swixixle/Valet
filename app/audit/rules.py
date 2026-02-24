from typing import List, Optional, Dict, Any
from app.audit.types import AuditStatus, AuditResult
from app.datasources.senate.senate_datasource import SenateDataSource
from app.datasources.senate.errors import SenateDataUnavailableError, SenateDataValidationError
import os
import json

ALLOWED_VOTE_VALUES = {"YEA", "NAY", "PRESENT", "NOT VOTING"}

def audit_vote_claim(senate: SenateDataSource, senator_id: str, bill_id: str) -> AuditResult:
    checks = []
    try:
        # Always scan all votes for this senator and bill
        try:
            all_votes = [e for e in senate.getVotesBySenator(senator_id) if e.get("bill_id") == bill_id]
        except Exception as e:
            return AuditResult(status=AuditStatus.INVALID_DATA, checks=[{"error": str(e)}])
        # Coverage check
        if not all_votes:
            checks.append({"coverage": False, "msg": "No vote event found for this bill and senator."})
            return AuditResult(status=AuditStatus.NO_RECORD, checks=checks)
        checks.append({"coverage": True, "count": len(all_votes)})
        # Uniqueness check
        vote_values = set(e.get("vote") for e in all_votes)
        if len(vote_values) > 1:
            checks.append({"uniqueness": False, "votes": list(vote_values)})
            return AuditResult(status=AuditStatus.AMBIGUOUS, checks=checks)
        checks.append({"uniqueness": True, "vote": list(vote_values)[0]})
        # Provenance check (all must have event_id and source_file)
        provenance_ok = all(bool(e.get("event_id")) and bool(e.get("source_file")) for e in all_votes)
        checks.append({"provenance": provenance_ok})
        # Schema/manifest version check
        manifest_ok = True
        manifest_path = os.path.join(senate.data_dir, "manifest.json") if senate.data_dir else None
        if manifest_path and os.path.exists(manifest_path):
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
                manifest_ok = "schema_version" in manifest
            except Exception:
                manifest_ok = False
        checks.append({"manifest": manifest_ok})
        if not provenance_ok or not manifest_ok:
            return AuditResult(status=AuditStatus.INVALID_DATA, checks=checks)
        return AuditResult(status=AuditStatus.VERIFIED, checks=checks)
    except (SenateDataUnavailableError, SenateDataValidationError) as e:
        return AuditResult(status=AuditStatus.INVALID_DATA, checks=[{"error": str(e)}])

def audit_dataset(senate: SenateDataSource) -> AuditResult:
    anomalies = []
    votes_by_key = {}
    all_events = []
    senator_ids = set()
    # Use only public APIs
    for senator in senate.listSenators():
        senator_id = senator["id"]
        senator_ids.add(senator_id)
        votes = senate.getVotesBySenator(senator_id)
        all_events.extend(votes)
        for event in votes:
            bid = event.get("bill_id")
            vote = event.get("vote")
            key = (bid, senator_id)
            votes_by_key.setdefault(key, set()).add(vote)
            # Invalid vote value
            if vote not in ALLOWED_VOTE_VALUES:
                anomalies.append({"invalid_vote": vote, "bill_id": bid, "senator_id": senator_id, "event_id": event.get("event_id")})
            # Missing timestamp
            if "timestamp" in event and not event.get("timestamp"):
                anomalies.append({"missing_timestamp": True, "event_id": event.get("event_id")})
    # After collecting all votes, check for conflicts
    for (bid, sid), votes in votes_by_key.items():
        if len(votes) > 1:
            anomalies.append({"conflict": True, "bill_id": bid, "senator_id": sid, "votes": list(votes)})
    checks = [{"total_events": len(all_events)}]
    return AuditResult(status=AuditStatus.VERIFIED if not anomalies else AuditStatus.INVALID_DATA, checks=checks, anomalies=anomalies)
