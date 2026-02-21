from __future__ import annotations

from .models import LayerScore


def analyze_pattern(article_input: object) -> LayerScore:
    try:
        from app.core.llm_client import call_llm
        import json
        import re

        text = getattr(article_input, "story_text", "") or getattr(article_input, "text", "") or ""
        outlet = getattr(article_input, "outlet", "") or ""
        system = (
            "You are a longitudinal media distortion pattern analyst. "
            "Respond with valid JSON only. "
            "Schema: {\"score\": <float 0.0-1.0>, \"confidence\": <float 0.0-1.0>, \"notes\": <string>}. "
            "Score represents repeated distortion pattern risk (0=low, 1=high)."
        )
        context = f"Outlet: {outlet}\n\n{text}" if outlet else text
        user = (
            "Analyze the following content for repeated distortion patterns: "
            "recurring misleading frames, systematic omission of context, "
            "and evidence of coordinated narrative pushing:\n\n" + context
        )
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
        return LayerScore(
            score=0.0,
            confidence=0.2,
            notes="Pattern analysis not yet connected to live data.",
        )
