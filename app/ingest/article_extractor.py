from __future__ import annotations

from .models import IngestResult


def extract_article(url: str) -> IngestResult:
    """
    Extract article text from a URL using trafilatura (preferred) or newspaper3k.
    Returns normalized plain text plus metadata.
    """
    try:
        import trafilatura
        from trafilatura.settings import use_config

        config = use_config()
        config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
        downloaded = trafilatura.fetch_url(url, config=config)
        if downloaded:
            result = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                with_metadata=True,
                output_format="python",
                config=config,
            )
            if result and isinstance(result, dict):
                text = result.get("text") or ""
                title = result.get("title")
                outlet = result.get("sitename")
                return IngestResult(
                    text=text,
                    source_type="article",
                    title=title,
                    outlet=outlet,
                    duration_seconds=None,
                    url=url,
                    word_count=len(text.split()),
                )
            # trafilatura returned plain text instead of dict
            text = trafilatura.extract(downloaded, config=config) or ""
            if text:
                return IngestResult(
                    text=text,
                    source_type="article",
                    title=None,
                    outlet=None,
                    duration_seconds=None,
                    url=url,
                    word_count=len(text.split()),
                )
    except ImportError:
        pass

    # Fallback: newspaper3k
    try:
        from newspaper import Article  # type: ignore[import-untyped]

        article = Article(url)
        article.download()
        article.parse()
        text = article.text or ""
        outlet = article.source_url or None
        return IngestResult(
            text=text,
            source_type="article",
            title=article.title or None,
            outlet=str(outlet) if outlet else None,
            duration_seconds=None,
            url=url,
            word_count=len(text.split()),
        )
    except ImportError:
        pass

    raise RuntimeError(
        "No article extraction library available. " "Install trafilatura>=1.6 or newspaper3k."
    )
