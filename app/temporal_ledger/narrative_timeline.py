from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NarrativeEvent:
    publication_date: datetime
    title: str
    source: str


@dataclass
class NarrativeTimeline:
    events: list[NarrativeEvent] = field(default_factory=list)

    def add_event(self, event: NarrativeEvent) -> None:
        self.events.append(event)
        self.events.sort(key=lambda e: e.publication_date)

    def in_window(self, start: datetime, end: datetime) -> list[NarrativeEvent]:
        return [e for e in self.events if start <= e.publication_date <= end]
