from __future__ import annotations

import pytest


def test_ingest_raw_text() -> None:
    from app.ingest.ingest import ingest

    result = ingest("You weren't distracted. You were designed.")

    assert result.source_type == "raw_text"
    assert result.text == "You weren't distracted. You were designed."
    assert result.url is None
    assert result.word_count == 6
    assert result.duration_seconds is None
    assert result.title is None
    assert result.outlet is None


def test_ingest_raw_text_word_count() -> None:
    from app.ingest.ingest import ingest

    text = " ".join(["word"] * 50)
    result = ingest(text)
    assert result.word_count == 50


def test_ingest_result_fields() -> None:
    from app.ingest.models import IngestResult

    r = IngestResult(
        text="hello world",
        source_type="article",
        title="Test Title",
        outlet="Test Outlet",
        duration_seconds=None,
        url="https://example.com",
        word_count=2,
    )
    assert r.text == "hello world"
    assert r.source_type == "article"
    assert r.title == "Test Title"
    assert r.outlet == "Test Outlet"
    assert r.duration_seconds is None
    assert r.url == "https://example.com"
    assert r.word_count == 2


def test_is_video_url() -> None:
    from app.ingest.video_extractor import is_video_url

    assert is_video_url("https://www.youtube.com/watch?v=abc")
    assert is_video_url("https://youtu.be/abc")
    assert is_video_url("https://www.tiktok.com/@user/video/123")
    assert is_video_url("https://twitter.com/user/status/123")
    assert is_video_url("https://x.com/user/status/123")
    assert not is_video_url("https://example.com/article")
    assert not is_video_url("https://news.bbc.co.uk/story")


def test_ingest_article_url_requires_library(monkeypatch: pytest.MonkeyPatch) -> None:
    """article_extractor raises RuntimeError when no extraction library is available."""
    import sys

    # Block trafilatura and newspaper imports
    monkeypatch.setitem(sys.modules, "trafilatura", None)  # type: ignore[arg-type]
    monkeypatch.setitem(sys.modules, "newspaper", None)  # type: ignore[arg-type]

    from app.ingest import article_extractor

    with pytest.raises(RuntimeError, match="No article extraction library available"):
        article_extractor.extract_article("https://example.com/article")


def test_ingest_video_url_requires_yt_dlp(monkeypatch: pytest.MonkeyPatch) -> None:
    """video_extractor raises RuntimeError when yt-dlp is not available."""
    import sys

    monkeypatch.setitem(sys.modules, "yt_dlp", None)  # type: ignore[arg-type]

    from app.ingest import video_extractor

    with pytest.raises(RuntimeError, match="yt-dlp is required"):
        video_extractor.extract_video("https://www.youtube.com/watch?v=abc")


def test_ingest_routes_video_url() -> None:
    """ingest() routes video URLs to video extractor (will fail without yt-dlp)."""
    from app.ingest.video_extractor import is_video_url

    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert is_video_url(url)


def test_ingest_routes_article_url() -> None:
    """ingest() routes non-video URLs to article extractor."""
    from app.ingest.video_extractor import is_video_url

    url = "https://www.nytimes.com/some-article"
    assert not is_video_url(url)
