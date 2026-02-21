from __future__ import annotations

from dataclasses import dataclass

_IMBALANCE_STATEMENT = "Coverage cluster imbalance detected across last {n} audits."
_DEFAULT_THRESHOLD = 0.60  # dominant cluster share above which imbalance is flagged


@dataclass
class ClusterBalanceResult:
    balanced: bool
    dominant_cluster: str | None
    dominant_share: float
    warning: str


def check_cluster_balance(
    cluster_counts: dict[str, int],
    threshold: float = _DEFAULT_THRESHOLD,
) -> ClusterBalanceResult:
    """Check whether any single cluster dominates *cluster_counts*.

    If one cluster accounts for more than *threshold* of all records, an
    imbalance warning is appended.  This protects analytical neutrality.
    """
    total = sum(cluster_counts.values())

    if total == 0:
        return ClusterBalanceResult(
            balanced=True,
            dominant_cluster=None,
            dominant_share=0.0,
            warning="",
        )

    dominant = max(cluster_counts, key=lambda k: cluster_counts[k])
    share = cluster_counts[dominant] / total

    if share > threshold:
        warning = _IMBALANCE_STATEMENT.format(n=total)
        return ClusterBalanceResult(
            balanced=False,
            dominant_cluster=dominant,
            dominant_share=round(share, 4),
            warning=warning,
        )

    return ClusterBalanceResult(
        balanced=True,
        dominant_cluster=dominant,
        dominant_share=round(share, 4),
        warning="",
    )
