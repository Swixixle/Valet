from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CoverageReport:
    political_cluster_counts: dict[str, int]
    industry_cluster_counts: dict[str, int]
    media_outlet_counts: dict[str, int]
    total_audits: int


def analyze_coverage(audit_records: list[dict]) -> CoverageReport:
    """Aggregate cluster and outlet frequencies across *audit_records*.

    Each record may contain:
    - ``political_cluster`` (str)
    - ``industry_cluster`` (str)
    - ``media_outlet`` (str)
    """
    political: dict[str, int] = {}
    industry: dict[str, int] = {}
    media: dict[str, int] = {}

    for record in audit_records:
        _increment(political, record.get("political_cluster", ""))
        _increment(industry, record.get("industry_cluster", ""))
        _increment(media, record.get("media_outlet", ""))

    return CoverageReport(
        political_cluster_counts=political,
        industry_cluster_counts=industry,
        media_outlet_counts=media,
        total_audits=len(audit_records),
    )


def _increment(d: dict[str, int], key: str) -> None:
    if key:
        d[key] = d.get(key, 0) + 1
