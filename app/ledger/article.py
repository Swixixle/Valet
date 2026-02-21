from __future__ import annotations

from .models import LayerScore


def analyze_article_content(article_input: object) -> LayerScore:
    # placeholder logic
    # later: integrate NLP-based content distortion scoring
    return LayerScore(
        score=0.0,
        confidence=0.2,
        notes="Article content analysis not yet connected to live data.",
    )
