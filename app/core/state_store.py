from __future__ import annotations

import hashlib
import json
from pathlib import Path

_STATE_FILE = "_valet/state.json"

_DEFAULT_STATE: dict = {
    "episode": 0,
    "prev_hash": None,
    "chain_id": "valet",
    "mood_bias": "rushed",
    "annoyance": 0.35,
    "existential": 0.40,
    "last_target": "The Valet",
    "last_slug": None,
    "last_run_utc": None,
}

_OPERATOR_CONTROL_LINE = "Operator-selected input. I didn't choose this—you handed it to me."
_CONTINUITY_LINE = "Episode {episode}. Chain {prev_short} → {cur_short}."
_NULL_HASH_PLACEHOLDER = "00000000"

# Mood drift coefficients
_ANNOYANCE_BASE = 0.02  # base drift per run
_ANNOYANCE_WEIGHT = 0.10  # distortion_score multiplier
_ANNOYANCE_RELIEF = 0.03  # constant relief per run
_ANNOYANCE_MIN_DRIFT = -0.05  # maximum annoyance decrease per run
_ANNOYANCE_MAX_DRIFT = 0.08  # maximum annoyance increase per run
_EXISTENTIAL_BASE = 0.01  # base existential drift per run
_EXISTENTIAL_WEIGHT = 0.15  # risk_score multiplier
_EXISTENTIAL_MAX_DRIFT = 0.06
_ANNOYANCE_DECAY = 0.98  # decay factor applied each run
_EXISTENTIAL_DECAY = 0.995  # decay factor applied each run

# Score scale: audit scores are 1–5; we normalise to [0, 1]
_MAX_SCORE_VALUE = 5.0


def load_state(dist_root: Path) -> dict:
    """Load persistent state from dist/_valet/state.json. Returns defaults if missing/corrupt."""
    state_path = dist_root / _STATE_FILE
    try:
        raw = state_path.read_text(encoding="utf-8")
        state = json.loads(raw)
        if not isinstance(state, dict):
            raise ValueError("State is not a dict")
        return {**_DEFAULT_STATE, **state}
    except Exception:
        return dict(_DEFAULT_STATE)


def save_state(dist_root: Path, state: dict) -> None:
    """Save state to dist/_valet/state.json."""
    state_path = dist_root / _STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def compute_story_fingerprint(story_text: str) -> str:
    """Compute sha256 of normalized story text."""
    normalized = " ".join(story_text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_run_hash(manifest: str) -> str:
    """Compute sha256 of manifest string."""
    return hashlib.sha256(manifest.encode("utf-8")).hexdigest()


def build_manifest(
    chain_id: str,
    episode: int,
    slug: str,
    mode: str,
    target: str | None,
    story_fingerprint: str,
    audit_fingerprint: str,
    prev_hash: str | None,
) -> str:
    """Build a canonical manifest string (ordered, newline-separated)."""
    lines = [
        chain_id,
        str(episode),
        slug,
        mode,
        target or "",
        story_fingerprint,
        audit_fingerprint,
        prev_hash or "",
    ]
    return "\n".join(lines)


def build_continuity_preamble(episode: int, prev_hash: str | None, current_hash: str) -> str:
    """Return the two-line continuity preamble."""
    prev_short = (prev_hash or _NULL_HASH_PLACEHOLDER)[:8]
    cur_short = current_hash[:8]
    continuity_line = _CONTINUITY_LINE.format(
        episode=episode, prev_short=prev_short, cur_short=cur_short
    )
    return f"{_OPERATOR_CONTROL_LINE}\n{continuity_line}"


def _mood_label(annoyance: float) -> str:
    if annoyance < 0.30:
        return "eager"
    if annoyance <= 0.65:
        return "rushed"
    return "annoyed"


def update_mood(state: dict, distortion_score: float, risk_score: float) -> dict:
    """Apply mood drift and return updated state."""
    annoyance = float(state["annoyance"])
    existential = float(state["existential"])
    annoyance_drift = _ANNOYANCE_BASE + _ANNOYANCE_WEIGHT * distortion_score - _ANNOYANCE_RELIEF
    annoyance += max(_ANNOYANCE_MIN_DRIFT, min(_ANNOYANCE_MAX_DRIFT, annoyance_drift))
    existential_drift = _EXISTENTIAL_BASE + _EXISTENTIAL_WEIGHT * risk_score
    existential += max(0.0, min(_EXISTENTIAL_MAX_DRIFT, existential_drift))
    annoyance *= _ANNOYANCE_DECAY
    existential *= _EXISTENTIAL_DECAY
    annoyance = max(0.0, min(1.0, annoyance))
    existential = max(0.0, min(1.0, existential))
    return {
        **state,
        "annoyance": round(annoyance, 4),
        "existential": round(existential, 4),
        "mood_bias": _mood_label(annoyance),
    }
