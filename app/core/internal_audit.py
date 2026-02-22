from __future__ import annotations

from dataclasses import dataclass, field

# Minimum aggregate confidence required to pass the data-completeness check.
_COMPLETENESS_THRESHOLD = 0.3


@dataclass
class InternalAuditResult:
    """Result of the pre-publish internal audit."""

    cluster_balance_ok: bool
    data_completeness_ok: bool
    language_bias_ok: bool
    violations: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return True only when all checks pass."""
        return self.cluster_balance_ok and self.data_completeness_ok and self.language_bias_ok

    @property
    def flagged_for_review(self) -> bool:
        return not self.passed


def check_cluster_balance(recent_targets: list[str] | None = None) -> bool:
    """Check that coverage is not drifting toward a single political or industry cluster.

    The full implementation requires a persistent coverage-frequency store.
    This stub always returns ``True`` (balanced) so the pipeline can proceed
    while that store is wired up.
    """
    return True


def check_data_completeness(confidence_score: float) -> bool:
    """Return ``True`` when aggregate confidence meets the minimum threshold."""
    return confidence_score >= _COMPLETENESS_THRESHOLD


def check_language_bias(text: str) -> bool:
    """Return ``True`` when no banned language is detected in *text*."""
    from app.core.language_constraints import enforce_language_constraints

    return not enforce_language_constraints(text)


def run_internal_audit(
    text: str,
    confidence_score: float,
    recent_targets: list[str] | None = None,
) -> InternalAuditResult:
    """Run all pre-publish internal audit checks and return a consolidated result.

    Parameters
    ----------
    text:
        The combined report text to scan for language bias.
    confidence_score:
        Aggregate confidence from the integrity ledger layers (0.0–1.0).
    recent_targets:
        Optional list of recent analysis targets used for cluster balance check.

    If any check fails the result's ``flagged_for_review`` property is ``True``
    and the violations list identifies which checks failed.
    """
    cluster_ok = check_cluster_balance(recent_targets)
    completeness_ok = check_data_completeness(confidence_score)
    language_ok = check_language_bias(text)

    violations: list[str] = []
    if not cluster_ok:
        violations.append("coverage_cluster_imbalance")
    if not completeness_ok:
        violations.append("data_completeness_below_threshold")
    if not language_ok:
        violations.append("language_bias_detected")

    return InternalAuditResult(
        cluster_balance_ok=cluster_ok,
        data_completeness_ok=completeness_ok,
        language_bias_ok=language_ok,
        violations=violations,
    )
