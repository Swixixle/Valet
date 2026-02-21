from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FRAME_W, FRAME_H = 720, 1280
FPS = 24
RECEIPT_DURATION_S = 2
JITTER_PX = 3


def _font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _draw_frame(text: str, hook: str, seed: str) -> np.ndarray:
    img = Image.new("RGB", (FRAME_W, FRAME_H), (15, 10, 25))
    draw = ImageDraw.Draw(img)

    title = _font(34)
    body = _font(44)

    draw.text((40, 40), "THE LOBBY", font=title, fill=(180, 140, 255))
    draw.text((40, 90), hook[:70], font=title, fill=(180, 180, 195))

    y = 360
    words = text.split()
    line = ""
    lines: list[str] = []
    for w in words:
        test = (line + " " + w).strip()
        if draw.textbbox((0, 0), test, font=body)[2] > FRAME_W - 80 and line:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)

    for ln in lines[:6]:
        draw.text((40, y), ln, font=body, fill=(245, 245, 255))
        y += 70

    draw.text((40, FRAME_H - 80), seed, font=title, fill=(120, 120, 140))
    return np.array(img)


def render_video_from_audit(
    audit: dict[str, Any], receipt_png: str | Path, out_dir: str | Path
) -> Path:
    from moviepy.editor import ImageClip, concatenate_videoclips  # type: ignore

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(audit["slug"])
    clips = []

    hook = audit["episode"]["hook"]
    for s in audit["episode"]["shots"]:
        frame = _draw_frame(s.get("text", ""), hook, audit["slug"][-8:])
        base = ImageClip(frame).set_duration(float(s.get("duration_s", 3)))

        duration = base.duration
        total_frames = int(duration * FPS)
        offsets = [
            (rng.randint(-JITTER_PX, JITTER_PX), rng.randint(-JITTER_PX, JITTER_PX))
            for _ in range(total_frames)
        ]

        def make_frame(t: float, _offsets=offsets, _frame=frame, _total=total_frames):
            idx = min(int(t * FPS), _total - 1)
            dx, dy = _offsets[idx]
            arr = _frame.copy()
            arr = np.roll(arr, dy, axis=0)
            arr = np.roll(arr, dx, axis=1)
            return arr

        clips.append(base.fl(lambda gf, t, _mf=make_frame: _mf(t)))

    receipt = Image.open(receipt_png).convert("RGB").resize((FRAME_W, FRAME_H))
    clips.append(ImageClip(np.array(receipt)).set_duration(RECEIPT_DURATION_S))

    final = concatenate_videoclips(clips, method="compose")
    out_path = Path(out_dir) / "video.mp4"
    final.write_videofile(str(out_path), fps=FPS, codec="libx264", audio=False, logger=None)
    return out_path
