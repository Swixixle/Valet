#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.pipeline_service import run_pipeline  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--file", "-f")
    g.add_argument("--text", "-t")
    p.add_argument("--mode", "-m", default="scalpel")
    p.add_argument("--target", default=None)
    args = p.parse_args()

    if args.file:
        story = Path(args.file).read_text(encoding="utf-8").strip()
    else:
        story = args.text.strip()

    result = run_pipeline(mode=args.mode, story_text=story, target=args.target)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
