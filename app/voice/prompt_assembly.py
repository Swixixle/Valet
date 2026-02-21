from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.voice.governance_loader import VoiceGovernance

_TEMPLATE = """\
# VOICE GOVERNANCE PAYLOAD (DO NOT DISCARD)
## CHARACTER
{character}

## VOICE BIBLE
{bible}

## ANCHOR LINES
{anchors}

## DRIFT (ANTI-EXAMPLES)
{drift}

## CALIBRATION / SELF-CHECK
{calibration}

# END VOICE GOVERNANCE PAYLOAD"""


def assemble_payload(gov: VoiceGovernance) -> str:
    return _TEMPLATE.format(
        character=gov.character,
        bible=gov.bible,
        anchors=gov.anchors,
        drift=gov.drift,
        calibration=gov.calibration,
    )
