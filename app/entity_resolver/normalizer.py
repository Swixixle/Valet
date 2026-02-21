from __future__ import annotations

import re

_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "esq", "phd", "md", "jd"}


def normalize_name(name: str) -> str:
    """Normalize a person or organization name for matching.

    - Lowercases
    - Strips punctuation
    - Removes known name suffixes
    - Collapses whitespace
    """
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r"[.,'\-]", " ", name)
    tokens = name.split()
    tokens = [t for t in tokens if t not in _SUFFIXES]
    return " ".join(tokens).strip()
