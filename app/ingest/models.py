from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IngestResult:
    text: str
    source_type: str  # "article" | "video" | "raw_text"
    title: str | None
    outlet: str | None
    duration_seconds: float | None  # None for articles / raw text
    url: str | None
    word_count: int
