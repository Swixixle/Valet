from __future__ import annotations


def test_internal_audit_passes_clean_text() -> None:
    from app.core.internal_audit import run_internal_audit

    result = run_internal_audit(text="Observable financial alignment.", confidence_score=0.7)
    assert result.passed is True
    assert result.flagged_for_review is False
    assert result.violations == []


def test_internal_audit_fails_on_banned_language() -> None:
    from app.core.internal_audit import run_internal_audit

    result = run_internal_audit(text="The official is corrupt.", confidence_score=0.7)
    assert result.language_bias_ok is False
    assert result.passed is False
    assert result.flagged_for_review is True
    assert "language_bias_detected" in result.violations


def test_internal_audit_fails_on_low_confidence() -> None:
    from app.core.internal_audit import run_internal_audit

    result = run_internal_audit(text="Observable alignment.", confidence_score=0.1)
    assert result.data_completeness_ok is False
    assert result.passed is False
    assert "data_completeness_below_threshold" in result.violations


def test_internal_audit_cluster_balance_check() -> None:
    from app.core.internal_audit import check_cluster_balance

    assert check_cluster_balance() is True
    assert check_cluster_balance(recent_targets=["outlet_a", "outlet_b"]) is True


def test_internal_audit_data_completeness_check() -> None:
    from app.core.internal_audit import check_data_completeness

    assert check_data_completeness(0.5) is True
    assert check_data_completeness(0.3) is True
    assert check_data_completeness(0.29) is False
    assert check_data_completeness(0.0) is False


def test_internal_audit_language_bias_check() -> None:
    from app.core.internal_audit import check_language_bias

    assert check_language_bias("Temporal alignment observed.") is True
    assert check_language_bias("This is criminal.") is False


def test_internal_audit_result_passed_property() -> None:
    from app.core.internal_audit import InternalAuditResult

    ok = InternalAuditResult(
        cluster_balance_ok=True, data_completeness_ok=True, language_bias_ok=True
    )
    assert ok.passed is True
    assert ok.flagged_for_review is False

    fail = InternalAuditResult(
        cluster_balance_ok=True,
        data_completeness_ok=False,
        language_bias_ok=True,
        violations=["data_completeness_below_threshold"],
    )
    assert fail.passed is False
    assert fail.flagged_for_review is True


def test_pipeline_audit_yaml_contains_epistemic_and_internal_audit(
    tmp_path,
    monkeypatch,
) -> None:
    """Pipeline output includes epistemic block and internal audit summary."""
    import yaml

    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="You weren't distracted. You were designed.",
        target=None,
    )

    with open(result["audit_yaml"], encoding="utf-8") as f:
        data = yaml.safe_load(f)

    audit = data["audit"]

    # Epistemic block must be present
    ep = audit["epistemic"]
    assert "confidence_score" in ep
    assert "data_completeness" in ep
    assert "transparency_level" in ep
    assert ep["transparency_level"] in (
        "FULLY_TRACEABLE",
        "PARTIALLY_TRACEABLE",
        "STRUCTURALLY_OPAQUE",
    )
    assert ep["causation_claim"] is False
    assert isinstance(ep["known_blind_zones"], list)

    # Internal audit block must be present
    ia = audit["internal_audit"]
    assert "passed" in ia
    assert "cluster_balance_ok" in ia
    assert "data_completeness_ok" in ia
    assert "language_bias_ok" in ia
    assert "violations" in ia
    assert "flagged_for_review" in ia
