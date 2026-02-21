from __future__ import annotations

from .models import LayerScore


def analyze_ownership(outlet: str) -> LayerScore:
    try:
        from app.core.llm_client import call_llm
        import json
        import re

        system = (
            "You are a media ownership analyst. Respond with valid JSON only. "
            "Schema: {\"score\": <float 0.0-1.0>, \"confidence\": <float 0.0-1.0>, \"notes\": <string>}. "
            "Score represents concentration of ownership risk (0=low, 1=high)."
        )
        user = (
            f"Analyze the ownership structure and known bias of this media outlet: {outlet!r}. "
            "Consider corporate ownership, known political alignment, and editorial independence risk."
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
            notes="Ownership mapping not yet connected to live data.",
        )
