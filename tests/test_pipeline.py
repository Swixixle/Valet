from __future__ import annotations

import json
from pathlib import Path

import yaml

_CANONICAL_METRICS = [
    "limbic_lure",
    "parrot_box",
    "opacity",
    "incentive_heat",
    "scale_distortion",
    "status_theater",
    "narrative_lock",
]


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

    audit = data["audit"]
    assert "audit" in data
    assert "scores" in audit
    assert len(audit["chosen_core_distortions"]) <= 3

    # clinical_recommendation must be present and non-empty in audit.yaml
    assert "clinical_recommendation" in audit
    assert audit["clinical_recommendation"]

    # canonical 7 metrics must all be present
    assert set(audit["scores"].keys()) == set(_CANONICAL_METRICS)

    # receipt.json must contain the same clinical_recommendation
    with open(r["receipt_json"], encoding="utf-8") as f:
        receipt = json.load(f)
    assert receipt.get("clinical_recommendation") == audit["clinical_recommendation"]


def test_golden_fixture_visibility(tmp_path: Path) -> None:
    """Golden fixture: 04-visibility.txt must produce the canonical clinical recommendation."""
    story_path = Path(__file__).parent.parent / "fixtures" / "stories" / "04-visibility.txt"
    story_text = story_path.read_text(encoding="utf-8").strip()

    from app.core.pipeline_service import run_pipeline

    r = run_pipeline(mode="scalpel", story_text=story_text, target=None)

    with open(r["audit_yaml"], encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["audit"]["clinical_recommendation"] == (
        "Volume is not a vital sign. Discharge when ready."
    )

    with open(r["receipt_json"], encoding="utf-8") as f:
        receipt = json.load(f)
    assert receipt["clinical_recommendation"] == (
        "Volume is not a vital sign. Discharge when ready."
    )
