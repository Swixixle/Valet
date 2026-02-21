from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

# ── Constants ──────────────────────────────────────────────────────────────────

EPISTEMIC_VERSION = "1.0"

_INCONCLUSIVE_STATEMENT = "The available public record is inconclusive."
_DEFAULT_THRESHOLD = 0.70

# Layer weights for weighted confidence aggregation.
# Ownership carries the most weight (0.25) because it reflects structural influence
# that is hardest to establish without full disclosure.  Pattern and regulatory
# are lowest (0.10 each) as they rely on observable behaviour alone.
LAYER_WEIGHTS: dict[str, float] = {
    "ownership": 0.25,
    "revenue": 0.20,
    "editorial": 0.15,
    "article": 0.20,
    "regulatory": 0.10,
    "pattern": 0.10,
}
_WEIGHT_FALLBACK = 1.0  # used for any layer not in the explicit table

# Confidence thresholds used for transparency tier assignment
_TIER_HIGH = 0.75
_TIER_MODERATE = 0.50


class DataCompleteness(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    MINIMAL = "minimal"
    UNKNOWN = "unknown"


class TransparencyTier(StrEnum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


# ── Public helpers ─────────────────────────────────────────────────────────────


def aggregate_layer_confidences(layer_confidences: dict[str, float | None]) -> float:
    """Return a weighted average confidence from *layer_confidences*.

    Any layer with a ``None`` confidence is excluded from both the numerator
    and the denominator so that missing data cannot silently drag the score
    toward zero or one.

    If all layers have ``None`` confidences the function returns ``0.0`` (most
    conservative assumption).
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for layer, conf in layer_confidences.items():
        if conf is None:
            continue
        w = LAYER_WEIGHTS.get(layer, _WEIGHT_FALLBACK)
        weighted_sum += conf * w
        total_weight += w

    if total_weight == 0.0:
        return 0.0

    return weighted_sum / total_weight


def _transparency_tier(confidence: float) -> TransparencyTier:
    if confidence >= _TIER_HIGH:
        return TransparencyTier.HIGH
    if confidence >= _TIER_MODERATE:
        return TransparencyTier.MODERATE
    return TransparencyTier.LOW


def _uncertainty_disclosure(
    confidence: float,
    data_completeness: DataCompleteness,
    entity_resolved: bool,
) -> str:
    parts: list[str] = []
    if confidence < _DEFAULT_THRESHOLD:
        parts.append(f"confidence {confidence:.0%} is below threshold {_DEFAULT_THRESHOLD:.0%}")
    if data_completeness != DataCompleteness.COMPLETE:
        parts.append(f"data completeness is {data_completeness.value}")
    if not entity_resolved:
        parts.append("entity resolution is ambiguous")
    if not parts:
        return "No material uncertainty flagged."
    return "Uncertainty factors: " + "; ".join(parts) + "."


def build_epistemic_block(
    confidence_score: float | None = None,
    layer_confidences: dict[str, float | None] | None = None,
    data_completeness: DataCompleteness = DataCompleteness.UNKNOWN,
    entity_resolved: bool = True,
) -> dict:
    """Build the standardised ``epistemic`` block for an audit output.

    If *layer_confidences* is supplied it takes precedence over
    *confidence_score* for the final score (using weighted average with null
    guards).  If both are omitted the confidence defaults to ``0.0``.

    Returns a plain :class:`dict` suitable for direct inclusion in the audit
    payload.
    """
    if layer_confidences is not None:
        score = aggregate_layer_confidences(layer_confidences)
    elif confidence_score is not None:
        score = float(confidence_score)
    else:
        score = 0.0

    tier = _transparency_tier(score)
    disclosure = _uncertainty_disclosure(score, data_completeness, entity_resolved)

    return {
        "epistemic_version": EPISTEMIC_VERSION,
        "confidence_score": round(score, 4),
        "data_completeness": data_completeness.value,
        "transparency_tier": tier.value,
        "uncertainty_disclosure": disclosure,
    }


# ── Legacy enforce_humility kept for backward compatibility ────────────────────


@dataclass
class EpistemicResult:
    output: dict
    humility_injected: bool
    reason: str


def enforce_humility(
    output: dict,
    *,
    confidence_score: float | None = None,
    data_complete: bool = True,
    entity_resolved: bool = True,
    threshold: float = _DEFAULT_THRESHOLD,
) -> EpistemicResult:
    """Inject an epistemic humility statement into *output* when warranted.

    Triggers when any of:
    - confidence_score is below *threshold*
    - data is marked incomplete
    - entity resolution is ambiguous

    Never allows silent assumptions.
    """
    reasons: list[str] = []

    if confidence_score is not None and confidence_score < threshold:
        reasons.append(f"confidence_score {confidence_score:.4f} < threshold {threshold}")

    if not data_complete:
        reasons.append("data_complete=False")

    if not entity_resolved:
        reasons.append("entity_resolved=False")

    if reasons:
        augmented = dict(output)
        augmented["humility_statement"] = _INCONCLUSIVE_STATEMENT
        return EpistemicResult(
            output=augmented,
            humility_injected=True,
            reason="; ".join(reasons),
        )

    return EpistemicResult(output=dict(output), humility_injected=False, reason="")
