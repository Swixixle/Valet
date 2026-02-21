from __future__ import annotations

from .models import LayerScore


def analyze_regulatory(article_input: object) -> LayerScore:
    # placeholder logic
    # later: integrate regulatory filing and compliance data
    return LayerScore(
        score=0.0,
        confidence=0.2,
        notes="Regulatory mapping not yet connected to live data.",
    )
