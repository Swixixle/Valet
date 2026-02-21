from __future__ import annotations


def test_enforce_language_constraints_clean_text() -> None:
    """Clean text returns an empty list (no violations)."""
    from app.core.language_constraints import enforce_language_constraints

    assert enforce_language_constraints("Observable financial alignment detected.") == []
    assert enforce_language_constraints("Temporal correlation within 30 days.") == []
    assert enforce_language_constraints("Data inconclusive.") == []


def test_enforce_language_constraints_detects_banned_phrases() -> None:
    """Each banned phrase is detected individually."""
    from app.core.language_constraints import BANNED_PHRASES, enforce_language_constraints

    for phrase in BANNED_PHRASES:
        violations = enforce_language_constraints(f"This content is {phrase}.")
        assert phrase in violations, f"Expected '{phrase}' to be flagged"


def test_enforce_language_constraints_case_insensitive() -> None:
    """Detection is case-insensitive."""
    from app.core.language_constraints import enforce_language_constraints

    assert "corrupt" in enforce_language_constraints("The official is CORRUPT.")
    assert "bribe" in enforce_language_constraints("Possible BRIBE involved.")


def test_enforce_language_constraints_multiple_violations() -> None:
    """Multiple banned phrases in one text are all reported."""
    from app.core.language_constraints import enforce_language_constraints

    text = "This is corrupt and criminal behaviour."
    violations = enforce_language_constraints(text)
    assert "corrupt" in violations
    assert "criminal" in violations


def test_enforce_language_constraints_empty_text() -> None:
    from app.core.language_constraints import enforce_language_constraints

    assert enforce_language_constraints("") == []


def test_banned_phrases_list_is_non_empty() -> None:
    from app.core.language_constraints import BANNED_PHRASES

    assert len(BANNED_PHRASES) >= 6
