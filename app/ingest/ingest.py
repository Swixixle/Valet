from __future__ import annotations

import re

from .article_extractor import extract_article
from .models import IngestResult
from .video_extractor import extract_video, is_video_url

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def ingest(source: str) -> IngestResult:
    """
    Accept a URL or raw text string.
    Detect source type and route to appropriate extractor.
    Return normalized plain text + metadata.
    """
    source = source.strip()
    if not _URL_RE.match(source):
        # Raw text passthrough
        return IngestResult(
            text=source,
            source_type="raw_text",
            title=None,
            outlet=None,
            duration_seconds=None,
            url=None,
            word_count=len(source.split()),
        )

    if is_video_url(source):
        return extract_video(source)

    return extract_article(source)
