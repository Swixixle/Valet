from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT_VOICE_LIBRARY_PATH = Path(__file__).resolve().parent.parent.parent.parent / "voice-library"


def _voice_library_root() -> Path:
    env = os.environ.get("VOICE_LIBRARY_PATH")
    if env:
        return Path(env)
    return _DEFAULT_VOICE_LIBRARY_PATH


@dataclass
class VoiceGovernance:
    character: str
    bible: str
    anchors: str
    calibration: str
    drift: str
    version_hint: str
    payload: str = field(init=False)

    def __post_init__(self) -> None:
        from app.voice.prompt_assembly import assemble_payload

        self.payload = assemble_payload(self)


def _read(path: Path, required: bool = True) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    if required:
        raise FileNotFoundError(f"Required voice-library file not found: {path}")
    return ""


def load_voice_governance(character: str, library_path: Path | None = None) -> VoiceGovernance:
    root = library_path if library_path is not None else _voice_library_root()

    bible = _read(root / "bible" / f"{character}_v1.md")
    anchors = _read(root / "anchors" / f"{character}_anchor_lines.txt")

    calibration_path = root / "calibration" / f"{character}_tone_check.md"
    if not calibration_path.exists():
        calibration_path = root / "calibration" / "tone_self_check_prompt.md"
    calibration = _read(calibration_path)

    drift_path = root / "drift" / f"{character}_drift_examples.txt"
    drift = _read(drift_path, required=False)

    version_hint = ""
    decision_log = root / "meta" / "decision_log.md"
    if decision_log.exists():
        version_hint = decision_log.read_text(encoding="utf-8").splitlines()[0].strip()

    return VoiceGovernance(
        character=character,
        bible=bible,
        anchors=anchors,
        calibration=calibration,
        drift=drift,
        version_hint=version_hint,
    )
