from __future__ import annotations

from .models import LayerScore


def analyze_revenue(outlet: str) -> LayerScore:
    try:
        from app.core.llm_client import call_llm
        import json
        import re

        system = (
            "You are a media revenue and advertiser conflict analyst. Respond with valid JSON only. "
            "Schema: {\"score\": <float 0.0-1.0>, \"confidence\": <float 0.0-1.0>, \"notes\": <string>}. "
            "Score represents advertiser/sponsor conflict risk (0=low, 1=high)."
        )
        user = (
            f"Analyze the known revenue model and advertiser/sponsor conflicts for "
            f"this media outlet: {outlet!r}. "
            "Consider dependence on advertising, known sponsor conflicts, and financial incentives to distort."
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
            notes="Revenue and advertiser mapping not yet connected to live data.",
        )
