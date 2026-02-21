from __future__ import annotations

import pytest


def test_calm_level_low_word_count() -> None:
    from app.core.time_pressure import compute_time_pressure

    tp = compute_time_pressure(word_count=50)
    assert tp.level == "CALM"
    assert "methodical" in tp.note.lower() or "30 seconds" in tp.note.lower()


def test_calm_level_boundary() -> None:
    from app.core.time_pressure import compute_time_pressure

    tp = compute_time_pressure(word_count=199)
    assert tp.level == "CALM"


def test_focused_level() -> None:
    from app.core.time_pressure import compute_time_pressure

    tp = compute_time_pressure(word_count=200)
    assert tp.level == "FOCUSED"

    tp2 = compute_time_pressure(word_count=500)
    assert tp2.level == "FOCUSED"

    tp3 = compute_time_pressure(word_count=799)
    assert tp3.level == "FOCUSED"


def test_pressured_level() -> None:
    from app.core.time_pressure import compute_time_pressure

    tp = compute_time_pressure(word_count=800)
    assert tp.level == "PRESSURED"

    tp2 = compute_time_pressure(word_count=2000)
    assert tp2.level == "PRESSURED"

    tp3 = compute_time_pressure(word_count=2999)
    assert tp3.level == "PRESSURED"


def test_critical_level() -> None:
    from app.core.time_pressure import compute_time_pressure

    tp = compute_time_pressure(word_count=3000)
    assert tp.level == "CRITICAL"

    tp2 = compute_time_pressure(word_count=10000)
    assert tp2.level == "CRITICAL"


def test_duration_overrides_to_higher_level() -> None:
    from app.core.time_pressure import compute_time_pressure

    # Long duration -> CRITICAL even with low word count
    tp = compute_time_pressure(word_count=10, duration_seconds=4000.0)
    assert tp.level == "CRITICAL"


def test_duration_focused() -> None:
    from app.core.time_pressure import compute_time_pressure

    tp = compute_time_pressure(word_count=0, duration_seconds=600.0)
    assert tp.level == "FOCUSED"


def test_duration_pressured() -> None:
    from app.core.time_pressure import compute_time_pressure

    tp = compute_time_pressure(word_count=0, duration_seconds=1800.0)
    assert tp.level == "PRESSURED"


def test_duration_critical() -> None:
    from app.core.time_pressure import compute_time_pressure

    tp = compute_time_pressure(word_count=0, duration_seconds=3700.0)
    assert tp.level == "CRITICAL"


def test_time_pressure_note_non_empty() -> None:
    from app.core.time_pressure import compute_time_pressure

    for wc in [100, 400, 1500, 5000]:
        tp = compute_time_pressure(word_count=wc)
        assert tp.note, f"note is empty for word_count={wc}"


def test_time_pressure_dataclass_fields() -> None:
    from app.core.time_pressure import TimePressure

    tp = TimePressure(level="CALM", note="Test note.")
    assert tp.level == "CALM"
    assert tp.note == "Test note."
