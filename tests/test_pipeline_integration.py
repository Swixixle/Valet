from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

_FIXTURE_STORY = (
    Path(__file__).parent.parent / "fixtures" / "stories" / "01-designed.txt"
)
_CANONICAL_METRICS = [
    "limbic_lure",
    "parrot_box",
    "opacity",
    "incentive_heat",
    "scale_distortion",
    "status_theater",
    "narrative_lock",
]


def test_pipeline_end_to_end_with_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end test using the 01-designed fixture. All output files must be created."""
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")
    story_text = _FIXTURE_STORY.read_text(encoding="utf-8").strip()

    result = pipeline_service.run_pipeline(mode="scalpel", story_text=story_text, target=None)

    assert Path(result["audit_yaml"]).exists()
    assert Path(result["receipt_json"]).exists()
    assert Path(result["receipt_png"]).exists()
    assert Path(result["video_mp4"]).exists()
    assert Path(result["integrity_ledger_json"]).exists()

    with open(result["audit_yaml"], encoding="utf-8") as f:
        data = yaml.safe_load(f)

    audit = data["audit"]
    assert set(audit["scores"].keys()) == set(_CANONICAL_METRICS)
    assert audit["clinical_recommendation"]
    assert len(audit["chosen_core_distortions"]) <= 3


def test_pipeline_scalpel_ledger_produces_but_if_video(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """scalpel-ledger mode must produce a but_if_video.mp4."""
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")
    story_text = _FIXTURE_STORY.read_text(encoding="utf-8").strip()

    result = pipeline_service.run_pipeline(
        mode="scalpel-ledger", story_text=story_text, target=None
    )

    assert "but_if_video_mp4" in result
    assert Path(result["but_if_video_mp4"]).exists()


def test_pipeline_passes_word_count_to_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_pipeline forwards word_count and duration_seconds to run_audit."""
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    calls: list[dict] = []
    original_run_audit = pipeline_service.run_audit

    def mock_run_audit(**kwargs):
        calls.append(kwargs)
        return original_run_audit(**kwargs)

    monkeypatch.setattr(pipeline_service, "run_audit", mock_run_audit)

    pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="Test story content.",
        word_count=3,
        duration_seconds=45.0,
    )

    assert len(calls) == 1
    assert calls[0]["word_count"] == 3
    assert calls[0]["duration_seconds"] == 45.0


def test_pipeline_result_contains_slug(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="You weren't distracted. You were designed.",
    )

    assert "slug" in result
    assert result["slug"]


def test_pipeline_scalpel_mode_no_but_if_video(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """scalpel mode (not scalpel-ledger) should NOT produce but_if_video_mp4."""
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="You weren't distracted. You were designed.",
    )

    assert "but_if_video_mp4" not in result


def test_pipeline_with_llm_mock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pipeline works correctly when LLM is mocked."""
    import json as _json

    from app.core import pipeline_service
    import app.core.llm_client as llm_mod

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    mock_audit_response = _json.dumps(
        {
            "scores": {
                m: {"score": 3, "why": "test why", "metaphor": "test meta"}
                for m in _CANONICAL_METRICS
            },
            "chosen_core_distortions": ["limbic_lure", "parrot_box", "opacity"],
            "clinical_recommendation": "LLM recommendation. Discharge when ready.",
            "episode": {
                "hook": "LLM hook.",
                "final_line": "LLM final line.",
                "cta": "LLM CTA.",
                "shots": [
                    {"index": i, "text": f"Shot {i}", "duration_s": 3} for i in range(1, 5)
                ],
            },
        }
    )
    mock_ledger_response = _json.dumps(
        {"score": 0.1, "confidence": 0.5, "notes": "Mock LLM analysis."}
    )

    def smart_mock(system_prompt: str, user_prompt: str) -> str:
        if "distortion metrics" in user_prompt:
            return mock_audit_response
        return mock_ledger_response

    monkeypatch.setattr(llm_mod, "call_llm", smart_mock)

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="You weren't distracted. You were designed.",
    )

    with open(result["audit_yaml"], encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["audit"]["clinical_recommendation"] == "LLM recommendation. Discharge when ready."
