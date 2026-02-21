from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LayerScore:
    score: float
    confidence: float
    notes: str


@dataclass
class DamageEstimate:
    scenario: str
    stakes: str
    episode: dict

    def __len__(self) -> int:
        return len(self.scenario) + len(self.stakes)


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

    damage_estimate: DamageEstimate | None
    methodology_version: str
