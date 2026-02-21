from __future__ import annotations

import logging
from dataclasses import dataclass

from .confidence_score import compute_confidence
from .normalizer import normalize_name

logger = logging.getLogger(__name__)

_DEFAULT_THRESHOLD = 0.80
_AMBIGUITY_LABEL = "Entity match inconclusive."


@dataclass
class EntityMatch:
    query: str
    candidate: str
    confidence: float
    resolved: bool
    note: str


def match_entities(
    query: str,
    candidates: list[str],
    threshold: float = _DEFAULT_THRESHOLD,
) -> list[EntityMatch]:
    """Match *query* against *candidates* using normalized name similarity.

    Matches with confidence >= threshold are resolved.
    Matches below threshold are flagged as inconclusive and logged for review.
    Ambiguous matches (confidence in (0, threshold)) are never auto-resolved.
    """
    norm_query = normalize_name(query)
    results: list[EntityMatch] = []

    for candidate in candidates:
        norm_candidate = normalize_name(candidate)
        score = compute_confidence(norm_query, norm_candidate)
        resolved = score >= threshold
        note = "" if resolved else _AMBIGUITY_LABEL

        if not resolved and score > 0.0:
            logger.info(
                "Ambiguous entity match logged for review: %r vs %r (%.4f)",
                query,
                candidate,
                score,
            )

        results.append(
            EntityMatch(
                query=query,
                candidate=candidate,
                confidence=score,
                resolved=resolved,
                note=note,
            )
        )

    return results
