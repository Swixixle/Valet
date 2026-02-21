from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest


def test_layer_score_fields() -> None:
    from app.ledger.models import LayerScore

    ls = LayerScore(score=0.5, confidence=0.8, notes="test note")
    assert ls.score == 0.5
    assert ls.confidence == 0.8
    assert ls.notes == "test note"


def test_integrity_ledger_result_fields() -> None:
    from app.ledger.models import IntegrityLedgerResult, LayerScore

    ls = LayerScore(score=0.0, confidence=0.2, notes="stub")
    result = IntegrityLedgerResult(
        outlet="test-outlet",
        article_id="test-id",
        ownership=ls,
        revenue=ls,
        editorial=ls,
        article=ls,
        regulatory=ls,
        pattern=ls,
        total_score=0.0,
        risk_level="LOW",
        damage_estimate=None,
        methodology_version="0.1-alpha",
    )
    assert result.outlet == "test-outlet"
    assert result.risk_level == "LOW"
    assert result.methodology_version == "0.1-alpha"


def test_layer_stubs_return_layer_scores() -> None:
    from app.ledger.article import analyze_article_content
    from app.ledger.editorial import analyze_editorial
    from app.ledger.models import LayerScore
    from app.ledger.ownership import analyze_ownership
    from app.ledger.pattern import analyze_pattern
    from app.ledger.regulatory import analyze_regulatory
    from app.ledger.revenue import analyze_revenue

    class _Stub:
        outlet = "outlet"
        id = "id"

    stub = _Stub()
    for result in [
        analyze_ownership("outlet"),
        analyze_revenue("outlet"),
        analyze_editorial(stub),
        analyze_article_content(stub),
        analyze_regulatory(stub),
        analyze_pattern(stub),
    ]:
        assert isinstance(result, LayerScore)
        assert isinstance(result.score, float)
        assert isinstance(result.confidence, float)
        assert isinstance(result.notes, str)


def test_run_integrity_ledger_returns_result() -> None:
    from app.ledger.models import IntegrityLedgerResult
    from app.ledger.scoring import run_integrity_ledger

    @dataclasses.dataclass
    class _Input:
        outlet: str = "test-outlet"
        id: str = "test-id"

    result = run_integrity_ledger(_Input())
    assert isinstance(result, IntegrityLedgerResult)
    assert result.outlet == "test-outlet"
    assert result.article_id == "test-id"
    assert result.risk_level in ("LOW", "MODERATE", "ELEVATED", "STRUCTURAL")
    assert result.damage_estimate is None
    assert result.methodology_version == "0.1-alpha"


def test_run_integrity_ledger_with_damage_estimate() -> None:
    from app.ledger.scoring import run_integrity_ledger

    @dataclasses.dataclass
    class _Input:
        outlet: str = "test-outlet"
        id: str = "test-id"

    result = run_integrity_ledger(_Input(), include_damage_estimate=True)
    assert result.damage_estimate is not None
    assert len(result.damage_estimate) > 0


def test_risk_levels() -> None:
    from app.ledger.scoring import _categorize

    assert _categorize(0.0) == "LOW"
    assert _categorize(0.24) == "LOW"
    assert _categorize(0.25) == "MODERATE"
    assert _categorize(0.49) == "MODERATE"
    assert _categorize(0.50) == "ELEVATED"
    assert _categorize(0.74) == "ELEVATED"
    assert _categorize(0.75) == "STRUCTURAL"
    assert _categorize(1.0) == "STRUCTURAL"


def test_pipeline_writes_integrity_ledger_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="You weren't distracted. You were designed.",
        target=None,
    )

    assert "integrity_ledger_json" in result
    ledger_path = Path(result["integrity_ledger_json"])
    assert ledger_path.exists()

    with open(ledger_path, encoding="utf-8") as f:
        ledger = json.load(f)

    assert "total_score" in ledger
    assert "risk_level" in ledger
    assert ledger["risk_level"] in ("LOW", "MODERATE", "ELEVATED", "STRUCTURAL")
    assert ledger["methodology_version"] == "0.1-alpha"


def test_pipeline_audit_yaml_contains_integrity_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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

    il = data["audit"]["integrity_ledger"]
    assert "total_score" in il
    assert "risk_level" in il
    assert "methodology_version" in il


def test_scalpel_ledger_mode_includes_damage_estimate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    result = pipeline_service.run_pipeline(
        mode="scalpel-ledger",
        story_text="You weren't distracted. You were designed.",
        target=None,
    )

    ledger_path = Path(result["integrity_ledger_json"])
    with open(ledger_path, encoding="utf-8") as f:
        ledger = json.load(f)

    assert ledger.get("damage_estimate") is not None
