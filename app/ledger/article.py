from __future__ import annotations

from .models import LayerScore


def _llm_analyze(prompt_topic: str, context: str) -> LayerScore:
    """Run an LLM-backed analysis. Falls back to stub if no LLM is configured."""
    try:
        from app.core.llm_client import call_llm

        system = (
            "You are a forensic media integrity analyst. Respond with valid JSON only. "
            "Schema: {\"score\": <float 0.0-1.0>, \"confidence\": <float 0.0-1.0>, \"notes\": <string>}"
        )
        user = f"Analyze the following for {prompt_topic}:\n\n{context}"
        import json
        import re

        raw = call_llm(system_prompt=system, user_prompt=user).strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw).strip()
        data: dict = json.loads(raw)
        return LayerScore(
            score=float(data["score"]),
            confidence=float(data["confidence"]),
            notes=str(data["notes"]),
        )
    except NotImplementedError:
        raise
    except Exception:
        raise


def analyze_article_content(article_input: object) -> LayerScore:
    text = getattr(article_input, "story_text", "") or getattr(article_input, "text", "") or ""
    outlet = getattr(article_input, "outlet", "") or ""
    context = f"Outlet: {outlet}\n\n{text}" if outlet else text
    try:
        return _llm_analyze(
            "factual integrity, unsupported claims, and content distortion", context
        )
    except NotImplementedError:
        return LayerScore(
            score=0.0,
            confidence=0.2,
            notes="Article content analysis not yet connected to live data.",
        )
