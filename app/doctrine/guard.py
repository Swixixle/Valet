from __future__ import annotations

import re
from dataclasses import dataclass

# Phrases that must never appear in published output.
# The system maps structure; it does not infer intent or assign moral scores.
BANNED_PHRASES: list[str] = [
    r"\bcorrupt\b",
    r"\bcorruption\b",
    r"\bconflict of interest\b",
    r"\billegal\b",
    r"\bcriminal\b",
    r"\bfraud\b",
    r"\bbribe\b",
    r"\bbribery\b",
    r"\bintent\b",
    r"\bintended to\b",
    r"\bguilt\b",
    r"\bguilty\b",
    r"\bproof of\b",
    r"\bmorally\b",
    r"\bimmoral\b",
    r"\bunethical\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in BANNED_PHRASES]


@dataclass
class DoctrineViolation:
    phrase_pattern: str
    matched_text: str
    position: int


def check_doctrine(text: str) -> list[DoctrineViolation]:
    """Scan *text* for banned phrases.

    Returns a list of DoctrineViolation objects.  An empty list means the
    text passes the non-accusation doctrine.

    This must be called before any audit output is published.
    """
    violations: list[DoctrineViolation] = []
    for pattern, compiled in zip(BANNED_PHRASES, _COMPILED, strict=True):
        for match in compiled.finditer(text):
            violations.append(
                DoctrineViolation(
                    phrase_pattern=pattern,
                    matched_text=match.group(),
                    position=match.start(),
                )
            )
    return violations
