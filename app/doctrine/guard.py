from __future__ import annotations

import re
from dataclasses import dataclass, field

# Phrases that must never appear in published output.
# The system maps structure; it does not infer intent or assign moral scores.
# Patterns are written as full-word regex so inflections are caught.
BANNED_PHRASES: list[str] = [
    r"\bcorrupt\w*\b",  # corrupt, corruption, corruptly, corrupted, corruptible
    r"\bconflict of interest\b",
    r"\billegal\w*\b",  # illegal, illegally, illegality
    r"\bcriminal\w*\b",  # criminal, criminally, criminality
    r"\bfraud\w*\b",  # fraud, fraudulent, fraudulently, fraudulence
    r"\bbribe\w*\b",  # bribe, bribery, bribing, bribed
    r"\bintended? to\b",  # intended to
    r"\bintent\b",  # intent (standalone)
    r"\bguilt\w*\b",  # guilt, guilty, guiltily
    r"\bproof of\b",
    r"\bmorally\b",
    r"\bimmoral\w*\b",  # immoral, immorally, immorality
    r"\bunethical\w*\b",  # unethical, unethically
]

# Loaded modifiers that signal hyperbole or accusatory tone.
# These trigger a soft warning (not a hard block) during publish checks.
LOADED_MODIFIERS: list[str] = [
    r"\brigged\b",
    r"\bshady\b",
    r"\bscheme\w*\b",
    r"\bscandalous\b",
    r"\bdishonest\b",
    r"\blying\b",
    r"\bmanipulat\w+\b",
    r"\bcover.?up\b",
    r"\bhide\b",
    r"\bhiding\b",
    r"\bsecretly\b",
    r"\bpay.?off\b",
    r"\bkickback\b",
    r"\bsell.?out\b",
    r"\bpuppet\b",
    r"\bpawn\b",
    r"\bexploit\w*\b",
]

_COMPILED_BANNED = [re.compile(p, re.IGNORECASE) for p in BANNED_PHRASES]
_COMPILED_LOADED = [re.compile(p, re.IGNORECASE) for p in LOADED_MODIFIERS]

# Keep backward-compatible alias
_COMPILED = _COMPILED_BANNED


@dataclass
class DoctrineViolation:
    phrase_pattern: str
    matched_text: str
    position: int


@dataclass
class LanguageConstraintResult:
    """Result of a full publish-surface language check."""

    violations: list[DoctrineViolation] = field(default_factory=list)
    loaded_modifier_warnings: list[DoctrineViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True when there are no hard doctrine violations."""
        return len(self.violations) == 0


def check_doctrine(text: str) -> list[DoctrineViolation]:
    """Scan *text* for banned phrases.

    Returns a list of DoctrineViolation objects.  An empty list means the
    text passes the non-accusation doctrine.

    This must be called before any audit output is published.
    """
    violations: list[DoctrineViolation] = []
    for pattern, compiled in zip(BANNED_PHRASES, _COMPILED_BANNED, strict=True):
        for match in compiled.finditer(text):
            violations.append(
                DoctrineViolation(
                    phrase_pattern=pattern,
                    matched_text=match.group(),
                    position=match.start(),
                )
            )
    return violations


def enforce_language_constraints(text: str) -> LanguageConstraintResult:
    """Run the full language constraint check for a single publish surface.

    Hard violations (banned phrases including inflections) are collected in
    ``result.violations``.  Soft warnings (loaded modifiers / tone-killers)
    are collected in ``result.loaded_modifier_warnings``.

    The caller must treat any non-empty ``violations`` list as a fatal error
    and abort publishing.  Loaded modifier warnings should be surfaced in the
    audit output for transparency.
    """
    violations = check_doctrine(text)

    warnings: list[DoctrineViolation] = []
    for pattern, compiled in zip(LOADED_MODIFIERS, _COMPILED_LOADED, strict=True):
        for match in compiled.finditer(text):
            warnings.append(
                DoctrineViolation(
                    phrase_pattern=pattern,
                    matched_text=match.group(),
                    position=match.start(),
                )
            )

    return LanguageConstraintResult(violations=violations, loaded_modifier_warnings=warnings)
