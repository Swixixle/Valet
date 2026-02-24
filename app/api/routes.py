from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator


from app.core.pipeline_service import DoctrineViolationError, run_pipeline
from app.api.dossier_vote_intent import is_senate_vote_query, extract_bill_id, extract_senator_name
from app.core.senate_context import SenateContext
from app.datasources.senate.errors import SenateDataUnavailableError

router = APIRouter()


class PipelineRequest(BaseModel):
    mode: str
    story_text: str | None = None
    target: str | None = None
    url: str | None = None

    @field_validator("mode")
    @classmethod
    def _mode_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("mode must not be empty")
        return v



@router.post("/pipeline")
def pipeline(req: PipelineRequest, request: Request):
    try:
        story_text = req.story_text
        word_count = 0
        duration_seconds: float | None = None

        audit_mode = request.query_params.get("audit", "false").lower() == "true"

        if req.url:
            from app.ingest.ingest import ingest
            ingested = ingest(req.url)
            story_text = ingested.text
            word_count = ingested.word_count
            duration_seconds = ingested.duration_seconds
        elif not story_text or not story_text.strip():
            raise ValueError("Either 'url' or 'story_text' must be provided and non-empty.")

        # Senate voting intent gate
        if is_senate_vote_query(story_text or ""):
            try:
                senate = SenateContext.get_instance()
                if not senate:
                    audit_block = {"status": "NO_RECORD", "checks": [], "anomalies": []} if audit_mode else None
                    resp = {"ok": False, "message": "No verified Senate record available."}
                    if audit_block:
                        resp["audit"] = audit_block
                    return resp
                senator_name = extract_senator_name(story_text or "")
                bill_id = extract_bill_id(story_text or "")
                senator_id = None
                senator_disp = None
                if senator_name:
                    matches = senate.searchSenators(senator_name)
                    if matches:
                        senator_id = matches[0]["id"]
                        senator_disp = matches[0]["name"]
                if not senator_id or not bill_id:
                    audit_block = {"status": "NO_RECORD", "checks": [], "anomalies": []} if audit_mode else None
                    resp = {"ok": False, "message": "No verified Senate record available."}
                    if audit_block:
                        resp["audit"] = audit_block
                    return resp
                event = senate.getVoteByBillAndSenator(bill_id, senator_id)
                if not event:
                    audit_block = {"status": "NO_RECORD", "checks": [], "anomalies": []} if audit_mode else None
                    resp = {"ok": False, "message": "No verified Senate record available."}
                    if audit_block:
                        resp["audit"] = audit_block
                    return resp
                answer = f"Senator {senator_disp or senator_name} voted {event['vote']} on {bill_id}."
                grounding = {
                    "event_id": event["event_id"],
                    "source_file": event.get("source_file"),
                    "timestamp": event.get("timestamp"),
                }
                resp = {
                    "ok": True,
                    "answer": answer,
                    "senator": {"id": senator_id, "name": senator_disp or senator_name},
                    "bill_id": bill_id,
                    "grounding": grounding,
                }
                if audit_mode:
                    audit_result = run_vote_audit(senate, senator_id, bill_id)
                    resp["audit"] = {
                        "status": audit_result.status.value,
                        "checks": audit_result.checks,
                        "anomalies": audit_result.anomalies or []
                    }
                return resp
            except SenateDataUnavailableError:
                audit_block = {"status": "INVALID_DATA", "checks": [], "anomalies": []} if audit_mode else None
                resp = {"ok": False, "message": "No verified Senate record available."}
                if audit_block:
                    resp["audit"] = audit_block
                return resp

        # Normal pipeline
        return run_pipeline(
            mode=req.mode,
            story_text=story_text or "",
            target=req.target,
            word_count=word_count,
            duration_seconds=duration_seconds,
        )
    except DoctrineViolationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "doctrine_violation",
                "surface": exc.surface,
                "violations": [
                    {"pattern": v.phrase_pattern, "matched": v.matched_text} for v in exc.violations
                ],
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
