from __future__ import annotations

AUDIT_SYSTEM_PROMPT = """\
You are a forensic content auditor. Your role is to analyze media content for factual \
distortions and intentional manipulation. You are precise, clinical, and direct. \
You do not editorialize. You identify distortions, score them, and produce a tightly \
scripted audit for a 30-second vertical video hosted by The Valet — a character who \
audits content like a hotel valet processes a receipt.

You MUST respond with valid JSON only. No prose before or after the JSON object.
"""

_METRIC_DEFINITIONS = {
    "limbic_lure": "Emotional manipulation — fear, outrage, or anxiety triggered without \
proportionate factual basis.",
    "parrot_box": "Repetition of talking points or slogans without supporting evidence or \
original analysis.",
    "opacity": "Deliberate vagueness, hidden sources, missing attribution, or suppressed context.",
    "incentive_heat": "Financial, political, or institutional incentive to distort the information.",  # noqa: E501
    "scale_distortion": "Making small things seem catastrophically large, or large things \
seem trivially small.",
    "status_theater": "Appeals to authority, credentials, or consensus without substantive \
backing.",
    "narrative_lock": "Presenting one interpretive frame as the only possible reading of events.",
}


def build_audit_user_prompt(
    story_text: str,
    governance_payload: str | None,
    duration_seconds: float | None,
    time_pressure_note: str,
) -> str:
    governance_section = f"\n\n---\n{governance_payload}\n---" if governance_payload else ""

    duration_context = ""
    if duration_seconds is not None:
        minutes = duration_seconds / 60
        duration_context = (
            f"\nSource duration: {minutes:.1f} minutes ({int(duration_seconds)} seconds)."
        )

    metrics_block = "\n".join(
        f"- {name}: {definition}" for name, definition in _METRIC_DEFINITIONS.items()
    )

    return f"""\
Audit the following content.{duration_context}
Time-pressure instruction: {time_pressure_note}
{governance_section}

## CONTENT TO AUDIT
{story_text}

## YOUR TASK
Score the content on each of the 7 distortion metrics below (1 = minimal, 5 = severe):
{metrics_block}

For each metric produce:
- score: integer 1–5
- why: plain English explanation (1–2 sentences)
- metaphor: a short, vivid metaphor in The Valet's voice

Then identify the top 3 distortions (highest scores), produce a clinical_recommendation \
in The Valet's voice (one sentence, clinical, slightly weary), and write the episode script.

The episode must fit 30 seconds of vertical video. Adjust language energy per the \
time-pressure instruction above.

Respond with this exact JSON schema (no other text):
{{
  "scores": {{
    "limbic_lure": {{"score": 1, "why": "...", "metaphor": "..."}},
    "parrot_box": {{"score": 1, "why": "...", "metaphor": "..."}},
    "opacity": {{"score": 1, "why": "...", "metaphor": "..."}},
    "incentive_heat": {{"score": 1, "why": "...", "metaphor": "..."}},
    "scale_distortion": {{"score": 1, "why": "...", "metaphor": "..."}},
    "status_theater": {{"score": 1, "why": "...", "metaphor": "..."}},
    "narrative_lock": {{"score": 1, "why": "...", "metaphor": "..."}}
  }},
  "chosen_core_distortions": ["metric1", "metric2", "metric3"],
  "clinical_recommendation": "...",
  "episode": {{
    "hook": "...",
    "final_line": "...",
    "cta": "...",
    "shots": [
      {{"index": 1, "text": "...", "duration_s": 3}},
      {{"index": 2, "text": "...", "duration_s": 3}},
      {{"index": 3, "text": "...", "duration_s": 3}},
      {{"index": 4, "text": "...", "duration_s": 3}}
    ]
  }}
}}"""
