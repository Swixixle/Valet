from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LayerScore:
    score: float
    confidence: float
    notes: str


@dataclass
class IntegrityLedgerResult:
    outlet: str
    article_id: str

    ownership: LayerScore
    revenue: LayerScore
    editorial: LayerScore
    article: LayerScore
    regulatory: LayerScore
    pattern: LayerScore

    total_score: float
    risk_level: str  # LOW / MODERATE / ELEVATED / STRUCTURAL

    damage_estimate: str | None
    methodology_version: str
