from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

FinancialEventKind = Literal[
    "board_appointment",
    "stock_acquisition",
    "donation",
    "lobbying_filing",
]


@dataclass
class FinancialEvent:
    timestamp: datetime
    kind: FinancialEventKind
    entity_id: str
    source_citation: str


@dataclass
class FinancialTimeline:
    events: list[FinancialEvent] = field(default_factory=list)

    def add_event(self, event: FinancialEvent) -> None:
        self.events.append(event)
        self.events.sort(key=lambda e: e.timestamp)

    def in_window(self, start: datetime, end: datetime) -> list[FinancialEvent]:
        return [e for e in self.events if start <= e.timestamp <= end]
