from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280


def _font(size: int, bold: bool = False):
    candidates = [
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ),
        (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
            if bold
            else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ),
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/Arial.ttf",
    ]
    for p in candidates:
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_receipt_from_audit(audit: dict[str, Any], out_dir: str | Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    receipt = audit["receipt"]
    json_path = out_dir / "receipt.json"
    json_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    img = Image.new("RGB", (W, H), (8, 8, 18))
    draw = ImageDraw.Draw(img)

    title = _font(44, bold=True)
    body = _font(26, bold=False)
    mono = _font(22, bold=False)

    draw.text((40, 40), "VALET STUDIO — LOBBY RECEIPT", font=title, fill=(180, 140, 255))
    y = 140
    draw.text((40, y), f"SLUG: {receipt['slug']}", font=mono, fill=(180, 180, 195))
    y += 40
    draw.text((40, y), f"MODE: {receipt['mode']}", font=mono, fill=(180, 180, 195))
    y += 60

    draw.text((40, y), f"\u201c{receipt['hook']}\u201d", font=body, fill=(245, 245, 255))
    y += 140

    draw.text((40, y), "TOP DISTORTIONS:", font=mono, fill=(180, 180, 195))
    y += 40
    for d in receipt["distortions_display"]:
        draw.text((60, y), f"- {d['id']}  ({d['score']}/5)", font=mono, fill=(245, 245, 255))
        y += 34

    stamp = _font(64, bold=True)
    draw.text((40, H - 220), receipt["lobby_stamp"], font=stamp, fill=(200, 60, 60))
    draw.text((40, H - 120), receipt["cta"], font=body, fill=(180, 140, 255))

    png_path = out_dir / "receipt.png"
    img.save(png_path, "PNG")
    return json_path, png_path
