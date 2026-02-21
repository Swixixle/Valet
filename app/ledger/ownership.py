from __future__ import annotations

from .models import LayerScore


def analyze_ownership(outlet: str) -> LayerScore:
    # placeholder logic
    # later: integrate ownership graph data
    return LayerScore(
        score=0.0,
        confidence=0.2,
        notes="Ownership mapping not yet connected to live data.",
    )
