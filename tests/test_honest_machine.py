"""Tests for Honest Machine v1.0 hardening:
- language constraint enforcement on all publish surfaces
- weighted epistemic block with null guards
- report contract validation
- internal audit block
- missing data disclosure
- doctrine-fatal pipeline abort
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ── doctrine / language constraints ───────────────────────────────────────────


def test_enforce_language_constraints_clean_text() -> None:
    from app.doctrine.guard import enforce_language_constraints

    result = enforce_language_constraints("The coverage was broad and the analysis was thorough.")
    assert result.passed
    assert result.violations == []
    assert result.loaded_modifier_warnings == []


def test_enforce_language_constraints_catches_banned_phrase() -> None:
    from app.doctrine.guard import enforce_language_constraints

    result = enforce_language_constraints("Evidence suggests corruption at the highest levels.")
    assert not result.passed
    assert len(result.violations) >= 1
    assert any("corrupt" in v.matched_text.lower() for v in result.violations)


def test_enforce_language_constraints_catches_inflections() -> None:
    from app.doctrine.guard import enforce_language_constraints

    # "fraudulently" is an inflection of "fraud" and must be caught
    result = enforce_language_constraints("Funds were fraudulently transferred.")
    assert not result.passed
    assert any("fraudulent" in v.matched_text.lower() for v in result.violations)


def test_enforce_language_constraints_soft_warns_loaded_modifier() -> None:
    from app.doctrine.guard import enforce_language_constraints

    result = enforce_language_constraints("The scheme appears to involve multiple parties.")
    # "scheme" is a loaded modifier: soft warning but not a hard violation
    assert result.passed
    assert len(result.loaded_modifier_warnings) >= 1
    assert any("scheme" in w.matched_text.lower() for w in result.loaded_modifier_warnings)


def test_enforce_language_constraints_catches_corruptly() -> None:
    from app.doctrine.guard import enforce_language_constraints

    result = enforce_language_constraints("The official acted corruptly.")
    assert not result.passed


def test_check_doctrine_backward_compat() -> None:
    """check_doctrine() still works and returns DoctrineViolation list."""
    from app.doctrine.guard import check_doctrine

    violations = check_doctrine("There is no illegal activity here.")
    assert len(violations) >= 1
    assert any("illegal" in v.matched_text.lower() for v in violations)


# ── epistemic block ────────────────────────────────────────────────────────────


def test_build_epistemic_block_versioned() -> None:
    from app.epistemic.enforcer import EPISTEMIC_VERSION, build_epistemic_block

    block = build_epistemic_block(confidence_score=0.8)
    assert block["epistemic_version"] == EPISTEMIC_VERSION
    assert "confidence_score" in block
    assert "data_completeness" in block
    assert "transparency_tier" in block
    assert "uncertainty_disclosure" in block


def test_build_epistemic_block_weighted_average() -> None:
    from app.epistemic.enforcer import build_epistemic_block

    layer_confidences = {
        "ownership": 0.9,
        "revenue": 0.8,
        "editorial": 0.7,
        "article": 0.6,
        "regulatory": 0.5,
        "pattern": 0.4,
    }
    block = build_epistemic_block(layer_confidences=layer_confidences)
    # Weighted average should be between min and max confidence
    assert 0.4 <= block["confidence_score"] <= 0.9


def test_build_epistemic_block_null_guards() -> None:
    from app.epistemic.enforcer import build_epistemic_block

    # None confidences must be excluded, not treated as 0
    layer_confidences = {
        "ownership": None,
        "revenue": None,
        "editorial": 0.8,
        "article": None,
        "regulatory": None,
        "pattern": None,
    }
    block = build_epistemic_block(layer_confidences=layer_confidences)
    # Only editorial (0.8) contributes; result should equal 0.8
    assert block["confidence_score"] == pytest.approx(0.8, abs=1e-4)


def test_build_epistemic_block_all_none_returns_zero() -> None:
    from app.epistemic.enforcer import build_epistemic_block

    block = build_epistemic_block(layer_confidences={"ownership": None, "revenue": None})
    assert block["confidence_score"] == 0.0


def test_aggregate_layer_confidences_weighted() -> None:
    from app.epistemic.enforcer import LAYER_WEIGHTS, aggregate_layer_confidences

    layer_confidences = {k: 1.0 for k in LAYER_WEIGHTS}
    score = aggregate_layer_confidences(layer_confidences)
    # All layers at 1.0 → weighted average is 1.0
    assert score == pytest.approx(1.0, abs=1e-6)


def test_transparency_tier_high() -> None:
    from app.epistemic.enforcer import build_epistemic_block

    block = build_epistemic_block(confidence_score=0.85)
    assert block["transparency_tier"] == "high"


def test_transparency_tier_low() -> None:
    from app.epistemic.enforcer import build_epistemic_block

    block = build_epistemic_block(confidence_score=0.30)
    assert block["transparency_tier"] == "low"


# ── report contract ────────────────────────────────────────────────────────────


def test_validate_report_contract_passes() -> None:
    from app.doctrine.contract import validate_report_contract

    audit = {
        "scores": {},
        "chosen_core_distortions": [],
        "clinical_recommendation": "ok",
        "episode": {},
        "receipt": {},
        "epistemic": {},
        "missing_data_disclosure": {},
        "internal_audit": {},
    }
    result = validate_report_contract(audit)
    assert result.passed
    assert result.missing_sections == []


def test_validate_report_contract_fails_missing_section() -> None:
    from app.doctrine.contract import validate_report_contract

    # Omit "epistemic" and "internal_audit"
    audit = {
        "scores": {},
        "chosen_core_distortions": [],
        "clinical_recommendation": "ok",
        "episode": {},
        "receipt": {},
        "missing_data_disclosure": {},
    }
    result = validate_report_contract(audit)
    assert not result.passed
    assert "epistemic" in result.missing_sections
    assert "internal_audit" in result.missing_sections


# ── missing data disclosure ────────────────────────────────────────────────────


def test_build_missing_data_disclosure_with_missing() -> None:
    from app.doctrine.contract import build_missing_data_disclosure

    mdd = build_missing_data_disclosure(
        inputs_used=["ownership", "revenue"],
        inputs_missing=["editorial", "pattern"],
    )
    assert "editorial" in mdd.missing_sources
    assert "pattern" in mdd.missing_sources
    assert len(mdd.known_blind_zones) > 0
    assert "confidence" in mdd.impact_statement.lower()


def test_build_missing_data_disclosure_no_missing() -> None:
    from app.doctrine.contract import build_missing_data_disclosure

    mdd = build_missing_data_disclosure(
        inputs_used=["ownership", "revenue", "editorial"],
        inputs_missing=[],
    )
    assert mdd.missing_sources == []
    assert "blind zones" in mdd.impact_statement.lower()


# ── internal audit block ───────────────────────────────────────────────────────


def test_build_internal_audit_block_all_pass() -> None:
    from app.internal_audit import build_internal_audit_block

    block = build_internal_audit_block(data_complete=True, doctrine_violations=[])
    assert block["doctrine_status"] == "PASS"
    assert block["data_completeness_status"] == "PASS"
    assert block["actions_required"] == []


def test_build_internal_audit_block_doctrine_fail() -> None:
    from app.doctrine.guard import DoctrineViolation
    from app.internal_audit import build_internal_audit_block

    violation = DoctrineViolation(
        phrase_pattern=r"\bcorrupt\w*\b", matched_text="corrupt", position=0
    )
    block = build_internal_audit_block(doctrine_violations=[violation])
    assert block["doctrine_status"] == "FAIL"
    assert len(block["actions_required"]) > 0


def test_build_internal_audit_block_cluster_imbalance() -> None:
    from app.internal_audit import build_internal_audit_block

    block = build_internal_audit_block(
        cluster_counts={"left": 10, "right": 1},
        data_complete=True,
        doctrine_violations=[],
    )
    assert block["cluster_balance_status"] == "FLAGGED"
    assert len(block["actions_required"]) > 0


# ── pipeline doctrine abort ────────────────────────────────────────────────────


def test_pipeline_doctrine_abort_writes_aborted_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pipeline must abort and write ABORTED.json when doctrine is violated."""
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    # Story text containing a banned phrase
    with pytest.raises(pipeline_service.DoctrineViolationError):
        pipeline_service.run_pipeline(
            mode="scalpel",
            story_text="There is clear evidence of corruption in the organisation.",
        )

    # ABORTED.json must exist in the output directory
    aborted_files = list((tmp_path / "dist").rglob("ABORTED.json"))
    assert len(aborted_files) == 1, "ABORTED.json was not created"

    import json

    aborted = json.loads(aborted_files[0].read_text(encoding="utf-8"))
    assert aborted["reason"] == "doctrine_violation"
    assert "violations" in aborted


def test_pipeline_doctrine_abort_no_video_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After doctrine abort, no video.mp4 should be written."""
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    with pytest.raises(pipeline_service.DoctrineViolationError):
        pipeline_service.run_pipeline(
            mode="scalpel",
            story_text="Officials acted illegally to conceal information.",
        )

    video_files = list((tmp_path / "dist").rglob("video.mp4"))
    assert video_files == [], "video.mp4 must not be written after doctrine abort"


def test_pipeline_includes_epistemic_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    import yaml

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="The data shows a clear pattern of behaviour over time.",
    )

    with open(result["audit_yaml"], encoding="utf-8") as f:
        data = yaml.safe_load(f)

    epistemic = data["audit"]["epistemic"]
    assert "epistemic_version" in epistemic
    assert "confidence_score" in epistemic
    assert "transparency_tier" in epistemic
    assert "data_completeness" in epistemic
    assert "uncertainty_disclosure" in epistemic


def test_pipeline_includes_internal_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    import yaml

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="The analysis reveals a pattern in public disclosures.",
    )

    with open(result["audit_yaml"], encoding="utf-8") as f:
        data = yaml.safe_load(f)

    ia = data["audit"]["internal_audit"]
    assert "cluster_balance_status" in ia
    assert "data_completeness_status" in ia
    assert "doctrine_status" in ia
    assert "actions_required" in ia
    assert ia["doctrine_status"] == "PASS"


def test_pipeline_includes_missing_data_disclosure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    import yaml

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="The report examines observable public record behaviour.",
    )

    with open(result["audit_yaml"], encoding="utf-8") as f:
        data = yaml.safe_load(f)

    mdd = data["audit"]["missing_data_disclosure"]
    assert "missing_sources" in mdd
    assert "known_blind_zones" in mdd
    assert "impact_statement" in mdd


# ── API returns 422 for doctrine violations ────────────────────────────────────


def test_api_returns_422_for_doctrine_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST /pipeline with banned text must return 422, not 500."""
    from fastapi.testclient import TestClient

    from app.api.server import app
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/pipeline",
        json={"mode": "scalpel", "story_text": "This is clearly fraudulent behaviour."},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "doctrine_violation"
    assert "violations" in detail
