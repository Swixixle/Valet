from __future__ import annotations

from .models import LayerScore


def analyze_revenue(outlet: str) -> LayerScore:
    # placeholder logic
    # later: integrate revenue and advertising data
    return LayerScore(
        score=0.0,
        confidence=0.2,
        notes="Revenue and advertiser mapping not yet connected to live data.",
    )
