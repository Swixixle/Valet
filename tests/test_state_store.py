from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# state_store unit tests
# ---------------------------------------------------------------------------


def test_load_state_defaults_when_missing(tmp_path: Path) -> None:
    from app.core.state_store import load_state

    state = load_state(tmp_path)
    assert state["episode"] == 0
    assert state["prev_hash"] is None
    assert state["chain_id"] == "valet"


def test_load_state_reinitializes_on_corrupt(tmp_path: Path) -> None:
    from app.core.state_store import load_state

    state_dir = tmp_path / "_valet"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text("NOT VALID JSON }{{{", encoding="utf-8")

    state = load_state(tmp_path)
    assert state["episode"] == 0
    assert state["prev_hash"] is None


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    from app.core.state_store import load_state, save_state

    state = load_state(tmp_path)
    state["episode"] = 7
    state["prev_hash"] = "abc123"
    save_state(tmp_path, state)

    loaded = load_state(tmp_path)
    assert loaded["episode"] == 7
    assert loaded["prev_hash"] == "abc123"


def test_compute_story_fingerprint_deterministic() -> None:
    from app.core.state_store import compute_story_fingerprint

    fp1 = compute_story_fingerprint("Hello   World")
    fp2 = compute_story_fingerprint("Hello World")
    # Both normalise to "hello world"
    assert fp1 == fp2
    assert len(fp1) == 64  # sha256 hex digest


def test_build_manifest_and_hash_deterministic() -> None:
    from app.core.state_store import build_manifest, compute_run_hash

    m = build_manifest(
        chain_id="valet",
        episode=1,
        slug="my-slug-abc12345",
        mode="scalpel",
        target="test",
        story_fingerprint="fp1",
        audit_fingerprint="fp2",
        prev_hash=None,
    )
    h1 = compute_run_hash(m)
    h2 = compute_run_hash(m)
    assert h1 == h2
    assert len(h1) == 64


def test_build_continuity_preamble_format() -> None:
    from app.core.state_store import build_continuity_preamble

    preamble = build_continuity_preamble(episode=3, prev_hash=None, current_hash="abcdef12345678")
    assert "Episode 3" in preamble
    assert "00000000" in preamble  # prev_hash is None → "00000000"
    assert "abcdef12" in preamble  # first 8 chars of current_hash
    assert "Operator-selected input" in preamble


def test_update_mood_stays_bounded() -> None:
    from app.core.state_store import _DEFAULT_STATE, update_mood

    state = dict(_DEFAULT_STATE)
    # High distortion and risk: annoyance/existential should not exceed 1.0
    for _ in range(100):
        state = update_mood(state, distortion_score=1.0, risk_score=1.0)
    assert 0.0 <= state["annoyance"] <= 1.0
    assert 0.0 <= state["existential"] <= 1.0

    # Low distortion and risk: should not go below 0.0
    for _ in range(100):
        state = update_mood(state, distortion_score=0.0, risk_score=0.0)
    assert 0.0 <= state["annoyance"] <= 1.0
    assert 0.0 <= state["existential"] <= 1.0


def test_mood_label_mapping() -> None:
    from app.core.state_store import _DEFAULT_STATE, update_mood

    state = {**_DEFAULT_STATE, "annoyance": 0.10}
    result = update_mood(state, 0.0, 0.0)
    assert result["mood_bias"] == "eager"

    state = {**_DEFAULT_STATE, "annoyance": 0.50}
    result = update_mood(state, 0.0, 0.0)
    assert result["mood_bias"] == "rushed"

    state = {**_DEFAULT_STATE, "annoyance": 0.80}
    result = update_mood(state, 0.0, 0.0)
    assert result["mood_bias"] == "annoyed"


# ---------------------------------------------------------------------------
# Acceptance-criteria integration tests
# ---------------------------------------------------------------------------


def test_first_run_creates_state_and_chain_in_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC 1: First run creates state.json; audit.yaml has chain with prev_hash=null."""
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="You weren't distracted. You were designed.",
        target="me",
    )

    # state.json must exist
    state_path = tmp_path / "dist" / "_valet" / "state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["episode"] == 1
    assert state["prev_hash"] is not None  # set to current_hash after first run

    # audit.yaml must have chain block
    with open(result["audit_yaml"], encoding="utf-8") as f:
        data = yaml.safe_load(f)
    chain = data["audit"]["chain"]
    assert chain["prev_hash"] is None
    assert chain["current_hash"] is not None
    assert chain["episode"] == 1

    # chain.json must exist
    assert Path(result["chain_json"]).exists()


def test_second_run_links_to_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC 2: Second run's prev_hash equals first run's current_hash; episode increments."""
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    story = "You weren't distracted. You were designed."

    # First run
    r1 = pipeline_service.run_pipeline(mode="scalpel", story_text=story, target="me")
    with open(r1["audit_yaml"], encoding="utf-8") as f:
        first_chain = yaml.safe_load(f)["audit"]["chain"]
    first_current_hash = first_chain["current_hash"]

    # Second run (same story — different hash because episode/prev_hash change)
    r2 = pipeline_service.run_pipeline(mode="scalpel", story_text=story, target="me")
    with open(r2["audit_yaml"], encoding="utf-8") as f:
        second_chain = yaml.safe_load(f)["audit"]["chain"]

    assert second_chain["prev_hash"] == first_current_hash
    assert second_chain["episode"] == 2


def test_corrupt_state_reinitializes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC 3: Corrupt state.json → pipeline still runs; state reinitializes."""
    from app.core import pipeline_service

    dist = tmp_path / "dist"
    monkeypatch.setattr(pipeline_service, "_DIST", dist)

    # Plant a corrupt state file
    state_dir = dist / "_valet"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text("}{CORRUPT", encoding="utf-8")

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="You weren't distracted. You were designed.",
    )

    assert Path(result["audit_yaml"]).exists()
    state = json.loads((state_dir / "state.json").read_text(encoding="utf-8"))
    assert state["episode"] == 1


def test_episode_increments_produce_different_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC 4: Same input run twice produces different current_hash due to episode/prev_hash."""
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    story = "You weren't distracted. You were designed."

    r1 = pipeline_service.run_pipeline(mode="scalpel", story_text=story)
    # Capture first hash before second run overwrites the same slug directory
    with open(r1["audit_yaml"], encoding="utf-8") as f:
        h1 = yaml.safe_load(f)["audit"]["chain"]["current_hash"]

    r2 = pipeline_service.run_pipeline(mode="scalpel", story_text=story)
    with open(r2["audit_yaml"], encoding="utf-8") as f:
        h2 = yaml.safe_load(f)["audit"]["chain"]["current_hash"]

    assert h1 != h2


def test_receipt_json_contains_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """receipt.json must include chain and operator_control blocks."""
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="You weren't distracted. You were designed.",
    )

    receipt = json.loads(Path(result["receipt_json"]).read_text(encoding="utf-8"))
    assert "chain" in receipt
    assert "operator_control" in receipt
    assert "preamble" in receipt["operator_control"]
    assert "Operator-selected input" in receipt["operator_control"]["preamble"]
