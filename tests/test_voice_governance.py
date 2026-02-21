from __future__ import annotations

from pathlib import Path

import pytest

_FIXTURE_LIBRARY = Path(__file__).parent / "fixtures" / "voice-library"


def test_loader_loads_known_files_for_valet() -> None:
    from app.voice.governance_loader import load_voice_governance

    gov = load_voice_governance("valet", library_path=_FIXTURE_LIBRARY)

    assert gov.character == "valet"
    assert gov.bible
    assert gov.anchors
    assert gov.calibration
    assert gov.drift  # fixture includes drift
    assert gov.payload


def test_loader_raises_for_missing_required_file() -> None:
    from app.voice.governance_loader import load_voice_governance

    with pytest.raises(FileNotFoundError):
        load_voice_governance("nonexistent_character", library_path=_FIXTURE_LIBRARY)


def test_assembly_contains_required_headers_in_order() -> None:
    from app.voice.governance_loader import load_voice_governance

    gov = load_voice_governance("valet", library_path=_FIXTURE_LIBRARY)
    payload = gov.payload

    headers = [
        "# VOICE GOVERNANCE PAYLOAD (DO NOT DISCARD)",
        "## CHARACTER",
        "## VOICE BIBLE",
        "## ANCHOR LINES",
        "## DRIFT (ANTI-EXAMPLES)",
        "## CALIBRATION / SELF-CHECK",
        "# END VOICE GOVERNANCE PAYLOAD",
    ]
    positions = [payload.index(h) for h in headers]
    assert positions == sorted(positions), "Headers are not in the expected order"


def test_pipeline_writes_voice_governance_txt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.voice.governance_loader as gl
    from app.core import pipeline_service

    monkeypatch.setattr(pipeline_service, "_DIST", tmp_path / "dist")
    monkeypatch.setattr(gl, "_voice_library_root", lambda: _FIXTURE_LIBRARY)

    result = pipeline_service.run_pipeline(
        mode="scalpel",
        story_text="The system was designed this way.",
        target="valet",
    )

    voice_file = Path(result["audit_yaml"]).parent / "voice_governance.txt"
    assert voice_file.exists(), "voice_governance.txt was not written"
    content = voice_file.read_text(encoding="utf-8")
    assert "# VOICE GOVERNANCE PAYLOAD" in content
