from __future__ import annotations

import dataclasses
import json

import pytest


def _make_ledger(risk_level: str = "LOW"):
    from app.ledger.models import IntegrityLedgerResult, LayerScore

    ls = LayerScore(score=0.1, confidence=0.5, notes="test")
    return IntegrityLedgerResult(
        outlet="test-outlet",
        article_id="test-id",
        ownership=ls,
        revenue=ls,
        editorial=ls,
        article=ls,
        regulatory=ls,
        pattern=ls,
        total_score=0.1,
        risk_level=risk_level,
        damage_estimate=None,
        methodology_version="0.1-alpha",
    )


def test_stub_damage_estimate_returns_damage_estimate() -> None:
    from app.ledger.but_if import generate_damage_estimate

    ledger = _make_ledger("LOW")
    result = generate_damage_estimate(ledger)

    from app.ledger.models import DamageEstimate

    assert isinstance(result, DamageEstimate)
    assert isinstance(result.scenario, str)
    assert len(result.scenario) > 0
    assert isinstance(result.stakes, str)
    assert len(result.stakes) > 0
    assert isinstance(result.episode, dict)
    assert "shots" in result.episode


def test_damage_estimate_len() -> None:
    from app.ledger.but_if import generate_damage_estimate

    ledger = _make_ledger("MODERATE")
    result = generate_damage_estimate(ledger)
    assert len(result) > 0


def test_damage_estimate_all_risk_levels() -> None:
    from app.ledger.but_if import generate_damage_estimate

    for risk in ("LOW", "MODERATE", "ELEVATED", "STRUCTURAL"):
        ledger = _make_ledger(risk)
        result = generate_damage_estimate(ledger)
        assert result.scenario
        assert result.stakes


def test_damage_estimate_episode_has_shots() -> None:
    from app.ledger.but_if import generate_damage_estimate

    ledger = _make_ledger("ELEVATED")
    result = generate_damage_estimate(ledger)
    shots = result.episode.get("shots", [])
    assert len(shots) > 0


def test_llm_damage_estimate_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """When LLM is configured, generate_damage_estimate parses the JSON response."""
    mock_response = json.dumps(
        {
            "scenario": "If true, public trust collapses within 6 months.",
            "stakes": "Democratic participation is at risk.",
            "episode": {
                "hook": "But if it were true — follow the line.",
                "final_line": "The perimeter holds. For now.",
                "cta": "Trace the consequence.",
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

    from app.ledger.but_if import generate_damage_estimate

    ledger = _make_ledger("STRUCTURAL")
    result = generate_damage_estimate(ledger)

    assert result.scenario == "If true, public trust collapses within 6 months."
    assert result.stakes == "Democratic participation is at risk."
    assert result.episode["hook"] == "But if it were true — follow the line."
    assert len(result.episode["shots"]) == 4


def test_damage_estimate_serialization() -> None:
    """DamageEstimate serializes correctly via dataclasses.asdict."""
    from app.ledger.but_if import generate_damage_estimate

    ledger = _make_ledger("LOW")
    result = generate_damage_estimate(ledger)
    d = dataclasses.asdict(result)
    assert "scenario" in d
    assert "stakes" in d
    assert "episode" in d
    assert len(d) == 3  # exactly 3 keys
