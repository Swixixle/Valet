from __future__ import annotations

from dataclasses import dataclass, field

# Sections that every published report must contain (keys in the audit dict).
# A section may be stubbed (value indicates "not implemented") but must not be absent.
_REQUIRED_SECTIONS: list[str] = [
    "scores",
    "chosen_core_distortions",
    "clinical_recommendation",
    "episode",
    "receipt",
    "epistemic",
    "missing_data_disclosure",
    "internal_audit",
]


@dataclass
class ReportContractResult:
    passed: bool
    missing_sections: list[str] = field(default_factory=list)


def validate_report_contract(audit: dict) -> ReportContractResult:
    """Check that all required sections are present in *audit*.

    Sections may contain stub/placeholder values; they must simply exist.
    Returns a :class:`ReportContractResult` where ``passed`` is ``True`` only
    when every required section key is present.
    """
    missing = [s for s in _REQUIRED_SECTIONS if s not in audit]
    return ReportContractResult(passed=len(missing) == 0, missing_sections=missing)


@dataclass
class MissingDataDisclosure:
    missing_sources: list[str]
    known_blind_zones: list[str]
    impact_statement: str


def build_missing_data_disclosure(
    inputs_used: list[str],
    inputs_missing: list[str],
) -> MissingDataDisclosure:
    """Build a structured disclosure of data gaps.

    *inputs_used* lists data sources that were actually queried.
    *inputs_missing* lists sources that could not be reached or were absent.

    The returned object enumerates missing sources, known structural blind
    zones that persist regardless of input, and an impact statement on
    confidence.
    """
    # Structural blind zones that are always present in public-record analysis
    known_blind_zones: list[str] = [
        "501(c)(4) donor identity (legally shielded)",
        "Private equity beneficial ownership chains",
        "Informal editorial pressure not captured in public filings",
        "Off-the-record source relationships",
    ]

    if inputs_missing:
        impact = (
            "These gaps reduce confidence in ownership alignment inference"
            " and may under-weight financial motive signals."
        )
    else:
        impact = (
            "No input data gaps identified; structural blind zones remain"
            " (see known_blind_zones)."
        )

    return MissingDataDisclosure(
        missing_sources=list(inputs_missing),
        known_blind_zones=known_blind_zones,
        impact_statement=impact,
    )
