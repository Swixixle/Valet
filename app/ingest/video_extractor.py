from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .models import IngestResult

_WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")

# Platforms supported by yt-dlp
_VIDEO_URL_PATTERNS = (
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "twitch.tv",
    "vimeo.com",
)


def is_video_url(url: str) -> bool:
    return any(pattern in url.lower() for pattern in _VIDEO_URL_PATTERNS)


def extract_video(url: str) -> IngestResult:
    """
    Download audio from a video URL using yt-dlp and transcribe with openai-whisper.
    Returns normalized plain text plus metadata.
    """
    try:
        import yt_dlp  # type: ignore[import-untyped]
    except ImportError as e:
        raise RuntimeError(
            "yt-dlp is required for video extraction. Install yt-dlp>=2024.1."
        ) from e

    try:
        import whisper  # type: ignore[import-untyped]
    except ImportError as e:
        raise RuntimeError(
            "openai-whisper is required for video transcription. Install openai-whisper>=20231117."
        ) from e

    with tempfile.TemporaryDirectory() as tmp_dir:
        audio_path = Path(tmp_dir) / "audio.%(ext)s"

        ydl_opts: dict = {
            "format": "bestaudio/best",
            "outtmpl": str(audio_path),
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "96",
                }
            ],
        }

        title: str | None = None
        channel: str | None = None
        duration_seconds: float | None = None

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                title = info.get("title")
                channel = info.get("channel") or info.get("uploader")
                duration_seconds = float(info["duration"]) if info.get("duration") else None

        # Find the downloaded audio file
        audio_files = list(Path(tmp_dir).glob("audio.*"))
        if not audio_files:
            raise RuntimeError(f"yt-dlp did not produce an audio file for URL: {url}")
        downloaded_audio = audio_files[0]

        model = whisper.load_model(_WHISPER_MODEL)
        result = model.transcribe(str(downloaded_audio))
        text: str = result.get("text", "") if isinstance(result, dict) else str(result)
        text = text.strip()

    return IngestResult(
        text=text,
        source_type="video",
        title=title,
        outlet=channel,
        duration_seconds=duration_seconds,
        url=url,
        word_count=len(text.split()),
    )
