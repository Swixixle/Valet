from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from .financial_timeline import FinancialTimeline
from .narrative_timeline import NarrativeTimeline

_DEFAULT_WINDOW_DAYS = 120
_DEFAULT_CONFIDENCE_THRESHOLD = 0.5


@dataclass
class AlignmentResult:
    observable_alignment: bool
    correlation_window_days: int
    confidence_score: float
    # Hard constraint: causation_claim is always False.
    causation_claim: bool = False

    def to_dict(self) -> dict:
        return {
            "observable_alignment": self.observable_alignment,
            "correlation_window_days": self.correlation_window_days,
            "confidence_score": self.confidence_score,
            "causation_claim": False,
        }


def analyze_alignment(
    narrative: NarrativeTimeline,
    financial: FinancialTimeline,
    window_days: int = _DEFAULT_WINDOW_DAYS,
) -> AlignmentResult:
    """Detect observable temporal alignment between narrative and financial events.

    Returns an AlignmentResult.  causation_claim is always False.
    """
    if not narrative.events or not financial.events:
        return AlignmentResult(
            observable_alignment=False,
            correlation_window_days=window_days,
            confidence_score=0.0,
        )

    aligned_pairs = 0
    total_pairs = 0

    for f_event in financial.events:
        window_start = f_event.timestamp - timedelta(days=window_days)
        window_end = f_event.timestamp + timedelta(days=window_days)
        n_events_in_window = narrative.in_window(window_start, window_end)
        total_pairs += 1
        if n_events_in_window:
            aligned_pairs += 1

    confidence = round(aligned_pairs / total_pairs, 4) if total_pairs else 0.0
    observable = confidence >= _DEFAULT_CONFIDENCE_THRESHOLD

    return AlignmentResult(
        observable_alignment=observable,
        correlation_window_days=window_days,
        confidence_score=confidence,
    )
