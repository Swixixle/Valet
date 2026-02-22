from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from app.core.pipeline_service import run_pipeline
from app.escrow.signing import verify_receipt_signature


def _latest_receipt_json(root: Path = Path("dist")) -> Path:
    candidates = list(root.glob("*/receipt.json"))
    if not candidates:
        raise FileNotFoundError("No receipt.json found under dist/. Run generation first.")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _run_multistep_demo(turns: int, mode: str, target: str | None) -> dict[str, Any]:
    if turns < 1:
        raise ValueError("--turns must be >= 1")

    base_prompt = "Explain why a signed receipt is better than a standard log."
    turn_results: list[dict[str, Any]] = []
    previous_turn_hash: str | None = None

    for turn in range(1, turns + 1):
        prompt = f"{base_prompt} (turn {turn})"
        result = run_pipeline(mode=mode, story_text=prompt, target=target)

        receipt_path = Path(result["receipt_json"])
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        signature_valid = verify_receipt_signature(receipt)

        chain_path = Path(result["chain_json"])
        chain = json.loads(chain_path.read_text(encoding="utf-8"))

        current_hash = chain.get("current_hash")
        prev_hash = chain.get("prev_hash")

        turn_results.append(
            {
                "turn": turn,
                "slug": result["slug"],
                "receipt_json": str(receipt_path),
                "chain_json": str(chain_path),
                "signature_valid": signature_valid,
                "chain": {
                    "prev_hash": prev_hash,
                    "current_hash": current_hash,
                    "parent": previous_turn_hash,
                    "conversation_hash": current_hash,
                },
            }
        )
        previous_turn_hash = current_hash if isinstance(current_hash, str) else previous_turn_hash

    return {
        "scenario": "multistep_demo",
        "turns": turns,
        "all_signatures_valid": all(t["signature_valid"] for t in turn_results),
        "results": turn_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate signed audit artifacts from a prompt/story text."
    )
    parser.add_argument("--prompt", help="Prompt/story text to audit.")
    parser.add_argument("--mode", default="scalpel", help="Pipeline mode (default: scalpel).")
    parser.add_argument("--target", default=None, help="Optional voice target.")
    parser.add_argument(
        "--scenario",
        default=None,
        help="Optional scenario runner. Supported: multistep_demo.",
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=3,
        help="Number of turns for scenario runs (default: 3).",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify an existing signed receipt; do not run generation.",
    )
    parser.add_argument(
        "--receipt-json",
        default=None,
        help="Path to receipt.json for --verify-only. Defaults to latest dist/*/receipt.json.",
    )
    parser.add_argument(
        "--signing-key",
        default=None,
        help="Optional RECEIPT_SIGNING_KEY override for this run.",
    )
    args = parser.parse_args()

    if args.signing_key:
        os.environ["RECEIPT_SIGNING_KEY"] = args.signing_key

    if args.verify_only:
        receipt_path = Path(args.receipt_json) if args.receipt_json else _latest_receipt_json()
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        result = {
            "receipt_json": str(receipt_path),
            "signature_valid": verify_receipt_signature(receipt),
        }
    else:
        if args.scenario:
            if args.scenario != "multistep_demo":
                raise ValueError("Unsupported --scenario. Supported: multistep_demo")
            result = _run_multistep_demo(turns=args.turns, mode=args.mode, target=args.target)
        else:
            if not args.prompt or not args.prompt.strip():
                raise ValueError("--prompt is required unless --verify-only is set.")
            result = run_pipeline(mode=args.mode, story_text=args.prompt.strip(), target=args.target)

            receipt_path = Path(result["receipt_json"])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            result["signature_valid"] = verify_receipt_signature(receipt)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
