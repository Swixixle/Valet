from __future__ import annotations

# Phrases that imply intent, guilt, or moral judgment and are prohibited
# in published reports. If any are detected, the report must be blocked.
BANNED_PHRASES: list[str] = [
    "corrupt",
    "conflict of interest",
    "quid pro quo",
    "bribe",
    "compromised",
    "criminal",
]


def enforce_language_constraints(output_text: str) -> list[str]:
    """Return a list of banned phrases found in *output_text*.

    An empty return value means the text passed. A non-empty return value
    means one or more banned phrases were detected and the report must be
    blocked from publishing until the violations are resolved.
    """
    lower = output_text.lower()
    return [phrase for phrase in BANNED_PHRASES if phrase in lower]
