from __future__ import annotations


def _token_overlap(a: str, b: str) -> float:
    """Jaccard similarity over whitespace-split tokens."""
    set_a = set(a.split())
    set_b = set(b.split())
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def compute_confidence(normalized_a: str, normalized_b: str) -> float:
    """Return a confidence score in [0.0, 1.0] for two normalized name strings.

    Uses token-level Jaccard similarity as a fast, deterministic measure.
    """
    if normalized_a == normalized_b:
        return 1.0
    return round(_token_overlap(normalized_a, normalized_b), 4)
