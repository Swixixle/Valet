from __future__ import annotations

import pytest

_CANONICAL_METRICS = [
    "limbic_lure",
    "parrot_box",
    "opacity",
    "incentive_heat",
    "scale_distortion",
    "status_theater",
    "narrative_lock",
]


def test_stub_audit_returns_expected_shape() -> None:
    """Stub audit (no LLM configured) returns the canonical dict shape."""
    from app.core.audit_service import run_audit

    result = run_audit(mode="scalpel", story_text="You weren't distracted. You were designed.")

    assert "slug" in result
    assert "scores" in result
    assert set(result["scores"].keys()) == set(_CANONICAL_METRICS)
    assert "chosen_core_distortions" in result
    assert len(result["chosen_core_distortions"]) <= 3
    assert "clinical_recommendation" in result
    assert result["clinical_recommendation"]
    assert "episode" in result
    assert "shots" in result["episode"]
    assert len(result["episode"]["shots"]) == 4
    assert "receipt" in result


def test_stub_audit_scores_range() -> None:
    from app.core.audit_service import run_audit

    result = run_audit(mode="scalpel", story_text="Test content here.")
    for metric, data in result["scores"].items():
        assert 1 <= data["score"] <= 5, f"Score for {metric} out of range"
        assert isinstance(data["why"], str)
        assert isinstance(data["metaphor"], str)


def test_audit_with_word_count_and_duration() -> None:
    """run_audit accepts word_count and duration_seconds without error."""
    from app.core.audit_service import run_audit

    result = run_audit(
        mode="scalpel",
        story_text="Short text.",
        word_count=2,
        duration_seconds=60.0,
    )
    assert "scores" in result


def test_llm_audit_uses_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """When LLM is configured, run_audit calls the LLM and parses the JSON response."""
    import json

    mock_response = json.dumps(
        {
            "scores": {m: {"score": 3, "why": "test why", "metaphor": "test metaphor"} for m in _CANONICAL_METRICS},
            "chosen_core_distortions": ["limbic_lure", "parrot_box", "opacity"],
            "clinical_recommendation": "Test recommendation. Discharge when ready.",
            "episode": {
                "hook": "Test hook.",
                "final_line": "Test final line.",
                "cta": "Test CTA.",
                "shots": [
                    {"index": 1, "text": "Shot 1", "duration_s": 3},
                    {"index": 2, "text": "Shot 2", "duration_s": 3},
                    {"index": 3, "text": "Shot 3", "duration_s": 3},
                    {"index": 4, "text": "Shot 4", "duration_s": 3},
                ],
            },
        }
    )

    import app.core.llm_client as llm_mod

    monkeypatch.setattr(llm_mod, "call_llm", lambda system_prompt, user_prompt: mock_response)

    from app.core.audit_service import _run_llm_audit

    result = _run_llm_audit(
        mode="scalpel",
        story_text="Test story for LLM audit.",
        target=None,
        word_count=5,
        duration_seconds=None,
    )

    assert set(result["scores"].keys()) == set(_CANONICAL_METRICS)
    assert result["scores"]["limbic_lure"]["score"] == 3
    assert result["clinical_recommendation"] == "Test recommendation. Discharge when ready."
    assert result["episode"]["hook"] == "Test hook."
    assert len(result["episode"]["shots"]) == 4


def test_llm_audit_strips_code_fences(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM response wrapped in markdown code fences is parsed correctly."""
    import json

    payload = {
        "scores": {m: {"score": 2, "why": "w", "metaphor": "m"} for m in _CANONICAL_METRICS},
        "chosen_core_distortions": ["limbic_lure"],
        "clinical_recommendation": "Noted.",
        "episode": {
            "hook": "h",
            "final_line": "f",
            "cta": "c",
            "shots": [{"index": i, "text": f"s{i}", "duration_s": 3} for i in range(1, 5)],
        },
    }
    mock_response = f"```json\n{json.dumps(payload)}\n```"

    import app.core.llm_client as llm_mod

    monkeypatch.setattr(llm_mod, "call_llm", lambda system_prompt, user_prompt: mock_response)

    from app.core.audit_service import _run_llm_audit

    result = _run_llm_audit(
        mode="scalpel",
        story_text="Test.",
        target=None,
        word_count=1,
        duration_seconds=None,
    )
    assert "scores" in result


def test_run_audit_falls_back_to_stub_when_no_llm() -> None:
    """run_audit falls back to stub when LLM raises NotImplementedError."""
    from app.core.audit_service import run_audit

    # No LLM_PROVIDER set in env, so NotImplementedError is raised -> stub fallback
    result = run_audit(mode="scalpel", story_text="Fallback test content.")
    assert "scores" in result
    assert set(result["scores"].keys()) == set(_CANONICAL_METRICS)
