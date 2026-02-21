from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.core.pipeline_service import DoctrineViolationError, run_pipeline

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
def pipeline(req: PipelineRequest):
    try:
        story_text = req.story_text
        word_count = 0
        duration_seconds: float | None = None

        if req.url:
            from app.ingest.ingest import ingest

            ingested = ingest(req.url)
            story_text = ingested.text
            word_count = ingested.word_count
            duration_seconds = ingested.duration_seconds
        elif not story_text or not story_text.strip():
            raise ValueError("Either 'url' or 'story_text' must be provided and non-empty.")

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
                    {"pattern": v.phrase_pattern, "matched": v.matched_text}
                    for v in exc.violations
                ],
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
