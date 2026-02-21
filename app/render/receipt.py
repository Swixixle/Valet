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
    discharge_font = _font(32, bold=True)
    section_font = _font(28, bold=True)

    draw.text((40, 40), "VALET STUDIO — LOBBY RECEIPT", font=title, fill=(180, 140, 255))
    y = 130
    draw.text((40, y), f"SLUG: {receipt['slug']}", font=mono, fill=(180, 180, 195))
    y += 34
    draw.text((40, y), f"MODE: {receipt['mode']}", font=mono, fill=(180, 180, 195))
    y += 50

    # Vitals: all distortion scores
    draw.text((40, y), "VITALS", font=section_font, fill=(120, 200, 255))
    y += 36
    for metric_id, metric_data in audit["scores"].items():
        label = f"{metric_id}:  {metric_data['score']}/5"
        draw.text((60, y), label, font=mono, fill=(200, 200, 215))
        y += 28
    y += 10

    # Primary Diagnosis: chosen core distortions
    draw.text((40, y), "PRIMARY DIAGNOSIS", font=section_font, fill=(255, 160, 80))
    y += 36
    for d in receipt["distortions_display"]:
        draw.text((60, y), f"- {d['id']}  ({d['score']}/5)", font=mono, fill=(245, 220, 180))
        y += 30
    y += 10

    # Clinical Notes: hook/final line from episode
    draw.text((40, y), "CLINICAL NOTES", font=section_font, fill=(140, 220, 140))
    y += 36
    draw.text((60, y), f"\u201c{receipt['hook']}\u201d", font=body, fill=(210, 245, 210))
    y += 60

    # Discharge Instructions: clinical_recommendation (most prominent block)
    y += 10
    draw.text((40, y), "DISCHARGE INSTRUCTIONS", font=section_font, fill=(255, 100, 100))
    y += 40
    words = receipt["clinical_recommendation"].split()
    line = ""
    lines: list[str] = []
    for w in words:
        test = (line + " " + w).strip()
        if draw.textbbox((0, 0), test, font=discharge_font)[2] > W - 80 and line:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    for ln in lines:
        draw.text((40, y), ln, font=discharge_font, fill=(255, 200, 200))
        y += 44

    stamp = _font(64, bold=True)
    draw.text((40, H - 220), receipt["lobby_stamp"], font=stamp, fill=(200, 60, 60))
    draw.text((40, H - 120), receipt["cta"], font=body, fill=(180, 140, 255))

    png_path = out_dir / "receipt.png"
    img.save(png_path, "PNG")
    return json_path, png_path
