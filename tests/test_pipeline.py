from __future__ import annotations

from pathlib import Path

import yaml


def test_pipeline_outputs_exist(tmp_path: Path) -> None:
    from app.core.pipeline_service import run_pipeline

    r = run_pipeline(
        mode="scalpel", story_text="You weren't distracted. You were designed.", target="me"
    )

    assert Path(r["audit_yaml"]).exists()
    assert Path(r["receipt_png"]).exists()
    assert Path(r["video_mp4"]).exists()

    with open(r["audit_yaml"], encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "audit" in data
    assert "scores" in data["audit"]
    assert len(data["audit"]["chosen_core_distortions"]) <= 3
