from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime

_METRICS = [
    "limbic_lure",
    "parrot_box",
    "opacity",
    "incentive_heat",
    "scale_distortion",
    "status_theater",
    "narrative_lock",
]


def _slug(mode: str, text: str) -> str:
    digest = hashlib.sha256(f"{mode}:{text}".encode()).hexdigest()[:8]
    words = re.sub(r"[^a-z0-9 ]", "", text.lower()).split()
    prefix = "-".join(words[:3]) if words else "story"
    return f"{prefix}-{digest}"


def run_audit(mode: str, story_text: str, target: str | None = None) -> dict:
    slug = _slug(mode, story_text)
    h = hashlib.sha256(slug.encode("utf-8")).digest()

    scores: dict[str, dict] = {}
    for i, m in enumerate(_METRICS):
        score = (h[i % len(h)] % 5) + 1
        scores[m] = {
            "score": int(score),
            "why": "Template audit (v0). Replace with LLM later.",
            "metaphor": "A stamped receipt sliding across the counter.",
        }

    chosen = sorted(_METRICS, key=lambda k: scores[k]["score"], reverse=True)[:3]

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", story_text.strip()) if s.strip()]
    hook = sentences[0] if sentences else story_text[:80]
    final_line = sentences[-1] if len(sentences) > 1 else "Check your receipt."

    shots = []
    for idx in range(4):
        text = sentences[idx] if idx < len(sentences) else ""
        shots.append({"index": idx + 1, "text": text, "duration_s": 3})

    episode = {
        "runtime_sec": 14,
        "hook": hook,
        "final_line": final_line,
        "cta": "Type PROCESSED to acknowledge.",
        "caption": "The Lobby audits daily. Submit your story.",
        "visual": "A clay hotel lobby. The Valet slides a receipt across the counter.",
        "style": {
            "medium": "stop-motion claymation",
            "lighting": "moody red + charcoal shadows",
            "motion": "subtle jitter",
        },
        "shots": shots,
        "audio": {"ambience": "low hum", "foley": "paper slide", "music": "none"},
    }

    timestamp = datetime.now(UTC).isoformat()

    receipt = {
        "slug": slug,
        "mode": mode,
        "target": target,
        "lobby_stamp": "PROCESSED",
        "distortions_display": [{"id": k, "score": scores[k]["score"]} for k in chosen],
        "cta": episode["cta"],
        "hook": hook,
        "final_line": final_line,
        "timestamp": timestamp,
    }

    return {
        "slug": slug,
        "mode": mode,
        "target": target,
        "story_text": story_text,
        "timestamp": timestamp,
        "scores": scores,
        "chosen_core_distortions": chosen,
        "episode": episode,
        "receipt": receipt,
    }
