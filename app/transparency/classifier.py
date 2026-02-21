from __future__ import annotations

from typing import Literal

TransparencyTier = Literal["FULLY_TRACEABLE", "PARTIALLY_TRACEABLE", "STRUCTURALLY_OPAQUE"]

# Entity type → transparency tier mapping.
# Opacity is a structural property — it is never interpreted as guilt.
_TYPE_MAP: dict[str, TransparencyTier] = {
    "public_company": "FULLY_TRACEABLE",
    "government_agency": "FULLY_TRACEABLE",
    "501c3": "FULLY_TRACEABLE",
    "501c4": "PARTIALLY_TRACEABLE",
    "501c6": "PARTIALLY_TRACEABLE",
    "pac": "PARTIALLY_TRACEABLE",
    "llc_disclosed": "PARTIALLY_TRACEABLE",
    "llc_undisclosed": "STRUCTURALLY_OPAQUE",
    "shell_company": "STRUCTURALLY_OPAQUE",
    "anonymous_trust": "STRUCTURALLY_OPAQUE",
}


def classify_transparency(entity: object) -> TransparencyTier:
    """Classify the transparency tier of *entity*.

    Reads ``entity.entity_type`` (str).  Unknown types default to
    STRUCTURALLY_OPAQUE to avoid false assurance.

    Never interprets opacity as guilt — only classifies visibility.
    """
    entity_type: str = getattr(entity, "entity_type", "").lower().replace("-", "_")
    return _TYPE_MAP.get(entity_type, "STRUCTURALLY_OPAQUE")
