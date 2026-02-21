from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from app.core.audit_service import run_audit
from app.core.state_store import (
    _MAX_SCORE_VALUE,
    build_continuity_preamble,
    build_manifest,
    compute_run_hash,
    compute_story_fingerprint,
    load_state,
    save_state,
    update_mood,
)
from app.doctrine.contract import build_missing_data_disclosure, validate_report_contract
from app.doctrine.guard import DoctrineViolation, enforce_language_constraints
from app.epistemic.enforcer import build_epistemic_block
from app.internal_audit import build_internal_audit_block
from app.ledger.scoring import run_integrity_ledger
from app.render.receipt import render_receipt_from_audit
from app.render.video import render_video_from_audit
from app.voice.governance_loader import load_voice_governance

_DIST = Path("dist")


class DoctrineViolationError(ValueError):
    """Raised when published text contains doctrine violations."""

    def __init__(self, surface: str, violations: list[DoctrineViolation]) -> None:
        self.surface = surface
        self.violations = violations
        details = ", ".join(f"'{v.matched_text}'" for v in violations)
        super().__init__(f"Doctrine violation in {surface!r}: {details}")


@dataclasses.dataclass
class _ArticleInput:
    outlet: str
    id: str


def _collect_publish_surfaces(audit: dict[str, Any]) -> dict[str, str]:
    """Return a mapping of surface-name → text for every publish surface."""
    surfaces: dict[str, str] = {}

    # story text (narrative input)
    surfaces["story_text"] = audit.get("story_text", "")

    # clinical recommendation
    surfaces["clinical_recommendation"] = audit.get("clinical_recommendation", "")

    # episode narration (all shot texts + hook + final_line)
    episode = audit.get("episode", {})
    shots_text = " ".join(s.get("text", "") for s in episode.get("shots", []))
    surfaces["narration_script"] = " ".join(
        filter(
            None,
            [episode.get("hook", ""), episode.get("final_line", ""), shots_text],
        )
    )

    # receipt text fields
    receipt = audit.get("receipt", {})
    surfaces["receipt_hook"] = receipt.get("hook", "")
    surfaces["receipt_clinical_recommendation"] = receipt.get("clinical_recommendation", "")
    surfaces["receipt_cta"] = receipt.get("cta", "")
    surfaces["receipt_final_line"] = receipt.get("final_line", "")

    return surfaces


def _enforce_all_surfaces(audit: dict[str, Any]) -> tuple[list[DoctrineViolation], list]:
    """Run language constraints over every publish surface.

    Returns ``(all_violations, all_warnings)`` across all surfaces.
    Raises :class:`DoctrineViolationError` on the first surface with a hard
    violation so that the pipeline aborts before writing final artifacts.
    """
    all_violations: list[DoctrineViolation] = []
    all_warnings: list = []

    for surface_name, text in _collect_publish_surfaces(audit).items():
        if not text:
            continue
        result = enforce_language_constraints(text)
        if result.violations:
            raise DoctrineViolationError(surface_name, result.violations)
        all_violations.extend(result.violations)
        all_warnings.extend(result.loaded_modifier_warnings)

    return all_violations, all_warnings


def run_pipeline(
    mode: str,
    story_text: str,
    target: str | None = None,
    word_count: int = 0,
    duration_seconds: float | None = None,
) -> dict[str, Any]:
    character = target or "valet"

    # Load persistent state and increment episode counter
    state = load_state(_DIST)
    state["episode"] = state["episode"] + 1
    episode_num: int = state["episode"]
    story_fingerprint = compute_story_fingerprint(story_text)

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
    effective_word_count = word_count or len(story_text.split())
    audit = run_audit(
        mode=audit_mode,
        story_text=story_text,
        target=target,
        word_count=effective_word_count,
        duration_seconds=duration_seconds,
    )
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

    # ── Epistemic block ────────────────────────────────────────────────────────
    layer_confidences: dict[str, float | None] = {
        "ownership": ledger.ownership.confidence,
        "revenue": ledger.revenue.confidence,
        "editorial": ledger.editorial.confidence,
        "article": ledger.article.confidence,
        "regulatory": ledger.regulatory.confidence,
        "pattern": ledger.pattern.confidence,
    }
    audit["epistemic"] = build_epistemic_block(layer_confidences=layer_confidences)

    # ── Missing data disclosure ────────────────────────────────────────────────
    inputs_used: list[str] = [k for k, v in layer_confidences.items() if v is not None]
    inputs_missing: list[str] = [k for k, v in layer_confidences.items() if v is None]
    mdd = build_missing_data_disclosure(inputs_used, inputs_missing)
    audit["missing_data_disclosure"] = {
        "missing_sources": mdd.missing_sources,
        "known_blind_zones": mdd.known_blind_zones,
        "impact_statement": mdd.impact_statement,
    }

    # ── Internal audit block ───────────────────────────────────────────────────
    audit["internal_audit"] = build_internal_audit_block(
        data_complete=len(inputs_missing) == 0,
    )

    # ── Language constraint enforcement across all publish surfaces ───────────
    # This must happen BEFORE any artifact is written.  A DoctrineViolationError
    # here aborts the pipeline; ABORTED.json is written and the error re-raised.
    try:
        _, loaded_warnings = _enforce_all_surfaces(audit)
        audit["internal_audit"]["doctrine_status"] = "PASS"
        if loaded_warnings:
            audit["internal_audit"]["loaded_modifier_warnings"] = [
                {"pattern": w.phrase_pattern, "matched": w.matched_text} for w in loaded_warnings
            ]
    except DoctrineViolationError as exc:
        # Doctrine failure: update internal_audit, write ABORTED.json, then raise
        audit["internal_audit"]["doctrine_status"] = "FAIL"
        audit["internal_audit"]["actions_required"].append(str(exc))
        aborted_path = out_dir / "ABORTED.json"
        aborted_path.write_text(
            json.dumps(
                {
                    "reason": "doctrine_violation",
                    "detail": str(exc),
                    "surface": exc.surface,
                    "violations": [
                        {"pattern": v.phrase_pattern, "matched": v.matched_text}
                        for v in exc.violations
                    ],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        raise

    # ── Validate report contract ───────────────────────────────────────────────
    contract = validate_report_contract(audit)
    if not contract.passed:
        # Soft: missing sections are logged in internal_audit but do not abort
        audit["internal_audit"]["missing_report_sections"] = contract.missing_sections
        audit["internal_audit"]["actions_required"].append(
            f"Missing required report sections: {contract.missing_sections}"
        )

    # --- Hash-chain and continuity metadata ---
    # Compute audit fingerprint before adding chain block
    audit_fingerprint = hashlib.sha256(
        json.dumps(audit, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    prev_hash: str | None = state.get("prev_hash")
    chain_id: str = state.get("chain_id", "valet")  # type: ignore[assignment]

    manifest = build_manifest(
        chain_id=chain_id,
        episode=episode_num,
        slug=slug,
        mode=mode,
        target=target,
        story_fingerprint=story_fingerprint,
        audit_fingerprint=audit_fingerprint,
        prev_hash=prev_hash,
    )
    current_hash = compute_run_hash(manifest)
    preamble = build_continuity_preamble(episode_num, prev_hash, current_hash)

    chain_block: dict[str, Any] = {
        "chain_id": chain_id,
        "episode": episode_num,
        "prev_hash": prev_hash,
        "current_hash": current_hash,
    }
    operator_control_block: dict[str, Any] = {"preamble": preamble}

    audit["chain"] = chain_block
    audit["operator_control"] = operator_control_block
    audit["receipt"]["chain"] = chain_block
    audit["receipt"]["operator_control"] = operator_control_block
    # --- end hash-chain ---

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

    # Write chain.json
    chain_json = out_dir / "chain.json"
    chain_json.write_text(
        json.dumps({"manifest": manifest, **chain_block}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Update and persist state
    distortion_score = sum(v["score"] for v in audit["scores"].values()) / (
        _MAX_SCORE_VALUE * len(audit["scores"])
    )
    state = update_mood(state, distortion_score, ledger.total_score)
    state["prev_hash"] = current_hash
    state["last_slug"] = slug
    state["last_run_utc"] = audit["timestamp"]
    if target:
        state["last_target"] = target
    save_state(_DIST, state)

    result: dict[str, Any] = {
        "slug": slug,
        "audit_yaml": str(audit_yaml),
        "receipt_json": str(receipt_json),
        "receipt_png": str(receipt_png),
        "video_mp4": str(video_mp4),
        "integrity_ledger_json": str(ledger_json),
        "chain_json": str(chain_json),
    }

    # Render But-If video for scalpel-ledger mode
    if mode == "scalpel-ledger" and ledger.damage_estimate is not None:
        from app.ledger.models import DamageEstimate

        damage = ledger.damage_estimate
        if isinstance(damage, DamageEstimate) and damage.episode:
            but_if_audit = dict(audit)
            but_if_audit["episode"] = dict(but_if_audit.get("episode", {}))
            but_if_audit["episode"].update(damage.episode)
            but_if_tmp_dir = out_dir / "_butif_tmp"
            but_if_tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_video_path = render_video_from_audit(but_if_audit, receipt_png, but_if_tmp_dir)
            but_if_video_mp4 = out_dir / "but_if_video.mp4"
            tmp_video_path.rename(but_if_video_mp4)
            result["but_if_video_mp4"] = str(but_if_video_mp4)

    return result
