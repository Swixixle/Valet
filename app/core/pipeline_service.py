from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import yaml

from app.core.audit_service import run_audit
from app.ledger.scoring import run_integrity_ledger
from app.render.receipt import render_receipt_from_audit
from app.render.video import render_video_from_audit
from app.voice.governance_loader import load_voice_governance

_DIST = Path("dist")


@dataclasses.dataclass
class _ArticleInput:
    outlet: str
    id: str


def run_pipeline(mode: str, story_text: str, target: str | None = None) -> dict[str, Any]:
    character = target or "valet"

    governance_payload: str | None = None
    voice_meta: dict[str, Any] = {
        "character": character,
        "source": "voice-library",
        "payload_file": None,
    }
    try:
        governance = load_voice_governance(character)
        voice_meta["payload_file"] = "voice_governance.txt"
        if governance.version_hint:
            voice_meta["version_hint"] = governance.version_hint
        governance_payload = governance.payload
    except FileNotFoundError:
        pass

    # "scalpel-ledger" is a pipeline mode; the underlying audit always runs as "scalpel"
    audit_mode = "scalpel" if mode == "scalpel-ledger" else mode
    audit = run_audit(mode=audit_mode, story_text=story_text, target=target)
    audit["voice"] = voice_meta

    slug = audit["slug"]
    out_dir = _DIST / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Run Integrity Ledger; damage estimate is enabled only for scalpel-ledger mode
    include_damage = mode == "scalpel-ledger"
    article_input = _ArticleInput(outlet=target or "", id=slug)
    ledger = run_integrity_ledger(article_input, include_damage_estimate=include_damage)
    ledger_dict = dataclasses.asdict(ledger)

    audit["integrity_ledger"] = {
        "total_score": ledger.total_score,
        "risk_level": ledger.risk_level,
        "methodology_version": ledger.methodology_version,
    }

    if governance_payload is not None:
        (out_dir / "voice_governance.txt").write_text(governance_payload, encoding="utf-8")

    ledger_json = out_dir / "integrity_ledger.json"
    ledger_json.write_text(json.dumps(ledger_dict, indent=2, ensure_ascii=False), encoding="utf-8")

    audit_yaml = out_dir / "audit.yaml"
    audit_yaml.write_text(
        yaml.dump({"audit": audit}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    receipt_json, receipt_png = render_receipt_from_audit(audit, out_dir)
    video_mp4 = render_video_from_audit(audit, receipt_png, out_dir)

    return {
        "slug": slug,
        "audit_yaml": str(audit_yaml),
        "receipt_json": str(receipt_json),
        "receipt_png": str(receipt_png),
        "video_mp4": str(video_mp4),
        "integrity_ledger_json": str(ledger_json),
    }
