from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def test_pipeline_schema_compatibility_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="You weren't distracted. You were designed.",
        target=None,
    )

    with open(result["audit_yaml"], encoding="utf-8") as f:
        audit = yaml.safe_load(f)["audit"]

    epistemic = audit["epistemic"]
    assert "transparency_tier" in epistemic
    assert "transparency_level" in epistemic

    internal_audit = audit["internal_audit"]
    for key in (
        "cluster_balance_status",
        "data_completeness_status",
        "doctrine_status",
        "actions_required",
        "passed",
        "cluster_balance_ok",
        "data_completeness_ok",
        "language_bias_ok",
        "violations",
        "flagged_for_review",
    ):
        assert key in internal_audit
