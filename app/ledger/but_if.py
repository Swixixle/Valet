from __future__ import annotations

import json
import re

from .models import DamageEstimate, IntegrityLedgerResult

_BUT_IF_SYSTEM_PROMPT = """\
You are writing the script for The Perimeter Walker — the character who narrates the \
alternate scenario video: "But If" this claim were actually true, what follows?

The Perimeter Walker is calm, unsettling, methodical. He does not editorialize. \
He traces consequences.

Respond with valid JSON only. No prose before or after the JSON object.
"""


def _build_but_if_prompt(
    ledger: IntegrityLedgerResult,
    governance_payload: str | None,
) -> str:
    governance_section = (
        f"\n\n---\n{governance_payload}\n---" if governance_payload else ""
    )
    distortions = [
        f"- {layer}: score={getattr(ledger, layer.replace('-', '_'), None).score if getattr(ledger, layer.replace('-', '_'), None) else 'N/A'}"
        for layer in ["ownership", "revenue", "editorial", "article", "regulatory", "pattern"]
    ]
    distortions_text = "\n".join(distortions)

    return f"""\
Given the following integrity ledger results:
Risk level: {ledger.risk_level}
Total score: {ledger.total_score:.3f}

Layer scores:
{distortions_text}
{governance_section}

Generate the But-If scenario: if the distortions identified above were actually true \
and went unchallenged, what follows?

Respond with this exact JSON schema (no other text):
{{
  "scenario": "What would follow if these distortions were real and unchallenged (2-3 sentences).",
  "stakes": "What is actually at risk (1-2 sentences).",
  "episode": {{
    "hook": "Opening line for the But-If video.",
    "final_line": "Closing line.",
    "cta": "Call to action.",
    "shots": [
      {{"index": 1, "text": "...", "duration_s": 3}},
      {{"index": 2, "text": "...", "duration_s": 3}},
      {{"index": 3, "text": "...", "duration_s": 3}},
      {{"index": 4, "text": "...", "duration_s": 3}}
    ]
  }}
}}"""


def _stub_damage_estimate(ledger: IntegrityLedgerResult) -> DamageEstimate:
    risk = ledger.risk_level
    if risk == "LOW":
        exposure = "< 50k readers"
        behavior_shift = "< 1%"
        confidence = "low"
    elif risk == "MODERATE":
        exposure = "50k–250k readers"
        behavior_shift = "1–3%"
        confidence = "moderate"
    elif risk == "ELEVATED":
        exposure = "250k–500k readers"
        behavior_shift = "2–7%"
        confidence = "moderate"
    else:  # STRUCTURAL
        exposure = "> 500k readers"
        behavior_shift = "5–15%"
        confidence = "moderate"

    scenario = (
        "Media framing of this type has been associated with measurable "
        f"behavioral shifts in peer-reviewed studies (confidence: {confidence}). "
        f"Estimated exposure range: {exposure}. "
        f"Projected behavior impact probability-adjusted range: {behavior_shift} shift."
    )
    stakes = f"At this risk level ({risk}), sustained distortion could shift public understanding measurably."
    episode: dict = {
        "hook": "But if it were true — follow the line.",
        "final_line": "The perimeter holds. For now.",
        "cta": "Trace the consequence.",
        "shots": [
            {"index": 1, "text": scenario[:80], "duration_s": 3},
            {"index": 2, "text": stakes[:80], "duration_s": 3},
            {"index": 3, "text": f"Risk level: {risk}.", "duration_s": 3},
            {"index": 4, "text": "The perimeter holds. For now.", "duration_s": 3},
        ],
    }
    return DamageEstimate(scenario=scenario, stakes=stakes, episode=episode)


def generate_damage_estimate(ledger_result: IntegrityLedgerResult) -> DamageEstimate:
    """
    Produce a structured damage estimate based on ledger scores.

    Uses The Perimeter Walker's voice to narrate the alternate scenario.
    Falls back to stub when no LLM provider is configured.
    """
    try:
        from app.core.llm_client import call_llm

        governance_payload: str | None = None
        try:
            from app.voice.governance_loader import load_voice_governance

            gov = load_voice_governance("perimeter_walker")
            governance_payload = gov.payload
        except FileNotFoundError:
            pass

        prompt = _build_but_if_prompt(ledger_result, governance_payload)
        raw = call_llm(system_prompt=_BUT_IF_SYSTEM_PROMPT, user_prompt=prompt).strip()

        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw).strip()

        data: dict = json.loads(raw)
        return DamageEstimate(
            scenario=str(data["scenario"]),
            stakes=str(data["stakes"]),
            episode=data["episode"],
        )
    except NotImplementedError:
        return _stub_damage_estimate(ledger_result)
