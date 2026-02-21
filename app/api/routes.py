from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.core.pipeline_service import run_pipeline

router = APIRouter()


class PipelineRequest(BaseModel):
    mode: str
    story_text: str
    target: str | None = None

    @field_validator("mode")
    @classmethod
    def _mode_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("mode must not be empty")
        return v

    @field_validator("story_text")
    @classmethod
    def _story_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("story_text must not be empty")
        return v


@router.post("/pipeline")
def pipeline(req: PipelineRequest):
    try:
        return run_pipeline(mode=req.mode, story_text=req.story_text, target=req.target)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
