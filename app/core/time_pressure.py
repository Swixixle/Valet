from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TimePressure:
    level: str  # "CALM" | "FOCUSED" | "PRESSURED" | "CRITICAL"
    note: str


_NOTES: dict[str, str] = {
    "CALM": (
        "You have 30 seconds and the content is short. Be methodical. "
        "You can afford to be precise."
    ),
    "FOCUSED": "Standard operating window. Pick your shots.",
    "PRESSURED": (
        "You have 30 seconds and too much content. Triage. "
        "Name the worst offender. Wave off the rest. Say there isn't time."
    ),
    "CRITICAL": (
        "You have 30 seconds and they gave you a feature film. "
        "You are not okay. Pick one thing. Say it. Get out."
    ),
}


_LEVEL_ORDER = {"CALM": 0, "FOCUSED": 1, "PRESSURED": 2, "CRITICAL": 3}


def _level_from_word_count(word_count: int) -> str:
    if word_count < 200:
        return "CALM"
    if word_count < 800:
        return "FOCUSED"
    if word_count < 3000:
        return "PRESSURED"
    return "CRITICAL"


def _level_from_duration(duration_seconds: float) -> str:
    if duration_seconds < 120:
        return "CALM"
    if duration_seconds < 1200:
        return "FOCUSED"
    if duration_seconds < 3600:
        return "PRESSURED"
    return "CRITICAL"


def compute_time_pressure(
    word_count: int, duration_seconds: float | None = None
) -> TimePressure:
    """
    Calculate how stressed The Valet is based on content length.

    Thresholds:
    - CALM:      word_count < 200  or  duration_seconds < 120
    - FOCUSED:   word_count 200–800  or  duration_seconds 120–1200
    - PRESSURED: word_count 800–3000  or  duration_seconds 1200–3600
    - CRITICAL:  word_count > 3000  or  duration_seconds > 3600

    When both word_count and duration_seconds are provided, the higher
    (more stressed) level wins.
    """
    wc_level = _level_from_word_count(word_count)
    if duration_seconds is not None:
        dur_level = _level_from_duration(duration_seconds)
        level = max(wc_level, dur_level, key=lambda l: _LEVEL_ORDER[l])
    else:
        level = wc_level

    return TimePressure(level=level, note=_NOTES[level])
