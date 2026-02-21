from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.core.audit_service import run_audit
from app.render.receipt import render_receipt_from_audit
from app.render.video import render_video_from_audit

_DIST = Path("dist")


def run_pipeline(mode: str, story_text: str, target: str | None = None) -> dict[str, Any]:
    audit = run_audit(mode=mode, story_text=story_text, target=target)
    slug = audit["slug"]
    out_dir = _DIST / slug
    out_dir.mkdir(parents=True, exist_ok=True)

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
    }
