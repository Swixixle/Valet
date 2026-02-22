from __future__ import annotations

from .cluster_balance import ClusterBalanceResult, check_cluster_balance
from .coverage_analyzer import CoverageReport, analyze_coverage


def build_internal_audit_block(
    cluster_counts: dict[str, int] | None = None,
    data_complete: bool = True,
    doctrine_violations: list | None = None,
) -> dict:
    """Build the ``internal_audit`` block for an audit output.

    Parameters
    ----------
    cluster_counts:
        Political/industry cluster tallies for balance checking.
        If ``None`` or empty, cluster balance defaults to balanced (unknown).
    data_complete:
        Whether all expected data sources were available.
    doctrine_violations:
        List of :class:`~app.doctrine.guard.DoctrineViolation` objects or any
        truthy sequence.  An empty list means doctrine passed.

    Returns a plain dict suitable for inclusion in the audit payload.
    """
    if cluster_counts:
        balance = check_cluster_balance(cluster_counts)
        cluster_status = "PASS" if balance.balanced else "FLAGGED"
    else:
        cluster_status = "UNKNOWN"

    data_completeness_status = "PASS" if data_complete else "FLAGGED"
    doctrine_status = "PASS" if not doctrine_violations else "FAIL"

    actions: list[str] = []
    if cluster_status == "FLAGGED":
        actions.append("Review cluster balance — dominant cluster may bias coverage.")
    if data_completeness_status == "FLAGGED":
        actions.append("Incomplete data: extend source coverage before republishing.")
    if doctrine_status == "FAIL":
        actions.append("Doctrine violation detected: remove banned language before publishing.")

    violations: list[str] = []
    if cluster_status == "FLAGGED":
        violations.append("coverage_cluster_imbalance")
    if data_completeness_status == "FLAGGED":
        violations.append("data_completeness_below_threshold")
    if doctrine_status == "FAIL":
        violations.append("language_bias_detected")

    cluster_balance_ok = cluster_status != "FLAGGED"
    data_completeness_ok = data_completeness_status != "FLAGGED"
    language_bias_ok = doctrine_status == "PASS"
    passed = cluster_balance_ok and data_completeness_ok and language_bias_ok

    return {
        "passed": passed,
        "cluster_balance_ok": cluster_balance_ok,
        "data_completeness_ok": data_completeness_ok,
        "language_bias_ok": language_bias_ok,
        "violations": violations,
        "flagged_for_review": not passed,
        "cluster_balance_status": cluster_status,
        "data_completeness_status": data_completeness_status,
        "doctrine_status": doctrine_status,
        "actions_required": actions,
    }


__all__ = [
    "analyze_coverage",
    "check_cluster_balance",
    "build_internal_audit_block",
    "ClusterBalanceResult",
    "CoverageReport",
]
