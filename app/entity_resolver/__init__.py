from __future__ import annotations

from .confidence_score import compute_confidence
from .matcher import EntityMatch, match_entities
from .normalizer import normalize_name

__all__ = ["EntityMatch", "compute_confidence", "match_entities", "normalize_name"]
