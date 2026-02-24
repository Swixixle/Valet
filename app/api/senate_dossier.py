from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.senate_context import SenateContext
from app.datasources.senate.errors import SenateDataUnavailableError
import re
from app.audit.runner import run_dataset_audit

router = APIRouter()

class SenateVoteQuery(BaseModel):
    senator: str | None = None  # name or id
    bill: str | None = None
    query: str | None = None  # fallback: free text

@router.post("/dossier/senate-vote")
def senate_vote(query: SenateVoteQuery):
    try:
        senate = SenateContext.get_instance()
        if not senate:
            return {"ok": False, "message": "No verified Senate record available."}

        senator_id = None
        bill_id = None
        senator_name = None
        # 1. Try direct id
        if query.senator:
            s = senate.getSenatorById(query.senator)
            if s:
                senator_id = s["id"]
                senator_name = s["name"]
            else:
                # Try name search
                matches = senate.searchSenators(query.senator)
                if matches:
                    senator_id = matches[0]["id"]
                    senator_name = matches[0]["name"]
        # 2. Try free text search
        if not senator_id and query.query:
            matches = senate.searchSenators(query.query)
            if matches:
                senator_id = matches[0]["id"]
                senator_name = matches[0]["name"]
        # 3. Bill id
        if query.bill:
            bill_id = query.bill.strip()
        elif query.query:
            m = re.search(r"\b(HR|H\.R\.|S|S\.)\s?(\d+)\b", query.query, re.I)
            if m:
                bill_id = m.group(0).replace(" ", "")
        if not senator_id or not bill_id:
            return {"ok": False, "message": "No verified Senate record available."}
        event = senate.getVoteByBillAndSenator(bill_id, senator_id)
        if not event:
            return {"ok": False, "message": "No verified Senate record available."}
        return {
            "ok": True,
            "vote": event["vote"],
            "senator": {"id": senator_id, "name": senator_name},
            "bill_id": bill_id,
            "grounding": {
                "event_id": event["event_id"],
                "source_file": event.get("source_file"),
                "timestamp": event.get("timestamp"),
            },
        }
    except SenateDataUnavailableError:
        return {"ok": False, "message": "No verified Senate record available."}

@router.post("/audit/senate")
def audit_senate():
    senate = SenateContext.get_instance()
    if not senate:
        # Fail-closed: no data
        return {"ok": False, "audit": {"status": "NO_RECORD", "checks": [], "anomalies": []}}
    result = run_dataset_audit(senate)
    return {"ok": True, "audit": {
        "status": result.status.value,
        "checks": result.checks,
        "anomalies": result.anomalies or []
    }}
