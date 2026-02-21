from __future__ import annotations

# Confidence threshold below which an uncertainty note is appended.
_CONFIDENCE_THRESHOLD = 0.5

# Known blind zones that the system cannot observe from public data alone.
KNOWN_BLIND_ZONES: list[str] = [
    "501(c)(4) organizations",
    "Family offices",
    "Anonymous donors",
    "Offshore structures",
]

_INCONCLUSIVE_NOTE = "The available public record is inconclusive."
_BLIND_ZONE_NOTE = "Additional funding channels may exist beyond public filings."


def classify_transparency(confidence: float) -> str:
    """Map a confidence score to a transparency classification label.

    Returns one of:
      - ``FULLY_TRACEABLE``      (confidence >= 0.8)
      - ``PARTIALLY_TRACEABLE``  (0.5 <= confidence < 0.8)
      - ``STRUCTURALLY_OPAQUE``  (confidence < 0.5)

    Opacity must never be interpreted as implying guilt.
    """
    if confidence >= 0.8:
        return "FULLY_TRACEABLE"
    if confidence >= 0.5:
        return "PARTIALLY_TRACEABLE"
    return "STRUCTURALLY_OPAQUE"


def build_epistemic_block(confidence_score: float, data_completeness: str) -> dict:
    """Build the epistemic metadata block that must accompany every report.

    Parameters
    ----------
    confidence_score:
        Aggregate confidence derived from the integrity ledger layers (0.0–1.0).
    data_completeness:
        Human-readable completeness label — e.g. ``"Full"``, ``"Partial"``,
        or ``"Sparse"``.

    Returns a dict with fields matching the output contract::

        {
          "confidence_score": float,
          "data_completeness": str,
          "transparency_level": str,
          "causation_claim": bool,
          "known_blind_zones": list[str],
          "blind_zone_note": str,
          # "uncertainty_note" present only when confidence < threshold
        }
    """
    block: dict = {
        "confidence_score": round(confidence_score, 4),
        "data_completeness": data_completeness,
        "transparency_level": classify_transparency(confidence_score),
        "causation_claim": False,
        "known_blind_zones": list(KNOWN_BLIND_ZONES),
        "blind_zone_note": _BLIND_ZONE_NOTE,
    }
    if confidence_score < _CONFIDENCE_THRESHOLD:
        block["uncertainty_note"] = _INCONCLUSIVE_NOTE
    return block


def derive_data_completeness(confidence_score: float) -> str:
    """Map aggregate confidence to a data-completeness label."""
    if confidence_score >= 0.7:
        return "Full"
    if confidence_score >= 0.4:
        return "Partial"
    return "Sparse"
