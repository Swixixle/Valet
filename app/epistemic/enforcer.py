from __future__ import annotations

from dataclasses import dataclass

_INCONCLUSIVE_STATEMENT = "The available public record is inconclusive."
_DEFAULT_THRESHOLD = 0.70


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
