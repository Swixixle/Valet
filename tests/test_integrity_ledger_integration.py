"""Integration tests: ledger wired into the pipeline, mode-gated damage estimate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


def test_scalpel_mode_writes_ledger_no_damage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="You weren't distracted. You were designed.",
        target=None,
    )

    # integrity_ledger.json must exist
    ledger_path = Path(result["integrity_ledger_json"])
    assert ledger_path.exists()

    with open(ledger_path, encoding="utf-8") as f:
        ledger = json.load(f)

    assert "total_score" in ledger
    assert "risk_level" in ledger

    # damage_estimate must be absent or null in scalpel mode
    assert ledger.get("damage_estimate") is None

    # audit.yaml must contain the integrity_ledger summary
    with open(result["audit_yaml"], encoding="utf-8") as f:
        data = yaml.safe_load(f)

    il = data["audit"]["integrity_ledger"]
    assert "total_score" in il
    assert "risk_level" in il
    assert "methodology_version" in il


def test_scalpel_ledger_mode_includes_damage_estimate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    story = "You weren't distracted. You were designed."

    result = pipeline_service.run_pipeline(
        mode="scalpel-ledger",
        story_text=story,
        target=None,
    )

    ledger_path = Path(result["integrity_ledger_json"])
    assert ledger_path.exists()

    with open(ledger_path, encoding="utf-8") as f:
        ledger = json.load(f)

    # damage_estimate must be present and non-empty in scalpel-ledger mode
    assert ledger.get("damage_estimate") is not None
    assert len(ledger["damage_estimate"]) > 0

    # slug must match the scalpel-mode run for the same input
    scalpel_result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text=story,
        target=None,
    )
    assert result["slug"] == scalpel_result["slug"]
