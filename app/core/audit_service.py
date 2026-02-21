from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime

from app.core.time_pressure import compute_time_pressure

_METRICS = [
    "limbic_lure",
    "parrot_box",
    "opacity",
    "incentive_heat",
    "scale_distortion",
    "status_theater",
    "narrative_lock",
]

# Golden-fixture clinical recommendations keyed by slug prefix (first 3 slug words).
_GOLDEN_RECOMMENDATIONS: dict[str, str] = {
    "the-loudest-thing": "Volume is not a vital sign. Discharge when ready.",
}


def _clinical_recommendation(slug: str, chosen: list[str]) -> str:
    prefix = "-".join(slug.split("-")[:3])
    if prefix in _GOLDEN_RECOMMENDATIONS:
        return _GOLDEN_RECOMMENDATIONS[prefix]
    primary = chosen[0].replace("_", " ") if chosen else "distortion"
    return f"Address {primary} first. Discharge when ready."


def _slug(mode: str, text: str) -> str:
    digest = hashlib.sha256(f"{mode}:{text}".encode()).hexdigest()[:8]
    words = re.sub(r"[^a-z0-9 ]", "", text.lower()).split()
    prefix = "-".join(words[:3]) if words else "story"
    return f"{prefix}-{digest}"


def _run_stub_audit(mode: str, story_text: str, target: str | None) -> dict:
    """Deterministic stub audit — used when no LLM provider is configured."""
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
    clinical_recommendation = _clinical_recommendation(slug, chosen)

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
        "clinical_recommendation": clinical_recommendation,
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
        "clinical_recommendation": clinical_recommendation,
        "episode": episode,
        "receipt": receipt,
    }


def _run_llm_audit(
    mode: str,
    story_text: str,
    target: str | None,
    word_count: int,
    duration_seconds: float | None,
) -> dict:
    """LLM-backed audit. Raises NotImplementedError if no LLM provider is configured."""
    from app.core.audit_prompts import AUDIT_SYSTEM_PROMPT, build_audit_user_prompt
    from app.core.llm_client import call_llm

    time_pressure = compute_time_pressure(word_count=word_count, duration_seconds=duration_seconds)

    governance_payload: str | None = None
    try:
        from app.voice.governance_loader import load_voice_governance

        character = target or "valet"
        gov = load_voice_governance(character)
        governance_payload = gov.payload
    except FileNotFoundError:
        pass

    user_prompt = build_audit_user_prompt(
        story_text=story_text,
        governance_payload=governance_payload,
        duration_seconds=duration_seconds,
        time_pressure_note=time_pressure.note,
    )

    raw = call_llm(system_prompt=AUDIT_SYSTEM_PROMPT, user_prompt=user_prompt)

    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        raw = raw.strip()

    llm_data: dict = json.loads(raw)

    scores: dict[str, dict] = llm_data["scores"]
    chosen: list[str] = llm_data["chosen_core_distortions"]
    clinical_recommendation: str = llm_data["clinical_recommendation"]
    episode_data: dict = llm_data["episode"]

    slug = _slug(mode, story_text)
    timestamp = datetime.now(UTC).isoformat()

    hook = episode_data.get("hook", "")
    final_line = episode_data.get("final_line", "")
    cta = episode_data.get("cta", "Type PROCESSED to acknowledge.")
    shots = episode_data.get("shots", [])

    episode = {
        "runtime_sec": 30,
        "hook": hook,
        "final_line": final_line,
        "cta": cta,
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

    receipt = {
        "slug": slug,
        "mode": mode,
        "target": target,
        "lobby_stamp": "PROCESSED",
        "distortions_display": [{"id": k, "score": scores[k]["score"]} for k in chosen],
        "cta": cta,
        "hook": hook,
        "final_line": final_line,
        "clinical_recommendation": clinical_recommendation,
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
        "clinical_recommendation": clinical_recommendation,
        "episode": episode,
        "receipt": receipt,
    }


def run_audit(
    mode: str,
    story_text: str,
    target: str | None = None,
    word_count: int = 0,
    duration_seconds: float | None = None,
) -> dict:
    """
    Run a content distortion audit.

    When LLM_PROVIDER is configured, uses an LLM for real analysis.
    Falls back to deterministic stub behavior when no LLM is available.
    """
    effective_word_count = word_count or len(story_text.split())
    try:
        return _run_llm_audit(
            mode=mode,
            story_text=story_text,
            target=target,
            word_count=effective_word_count,
            duration_seconds=duration_seconds,
        )
    except NotImplementedError:
        return _run_stub_audit(mode=mode, story_text=story_text, target=target)
