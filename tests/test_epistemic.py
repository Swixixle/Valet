from __future__ import annotations


def test_classify_transparency_fully_traceable() -> None:
    from app.core.epistemic import classify_transparency

    assert classify_transparency(0.8) == "FULLY_TRACEABLE"
    assert classify_transparency(1.0) == "FULLY_TRACEABLE"
    assert classify_transparency(0.95) == "FULLY_TRACEABLE"


def test_classify_transparency_partially_traceable() -> None:
    from app.core.epistemic import classify_transparency

    assert classify_transparency(0.5) == "PARTIALLY_TRACEABLE"
    assert classify_transparency(0.75) == "PARTIALLY_TRACEABLE"
    assert classify_transparency(0.799) == "PARTIALLY_TRACEABLE"


def test_classify_transparency_structurally_opaque() -> None:
    from app.core.epistemic import classify_transparency

    assert classify_transparency(0.0) == "STRUCTURALLY_OPAQUE"
    assert classify_transparency(0.3) == "STRUCTURALLY_OPAQUE"
    assert classify_transparency(0.499) == "STRUCTURALLY_OPAQUE"


def test_build_epistemic_block_required_fields() -> None:
    from app.core.epistemic import build_epistemic_block

    block = build_epistemic_block(confidence_score=0.74, data_completeness="Partial")
    assert block["confidence_score"] == 0.74
    assert block["data_completeness"] == "Partial"
    assert block["transparency_level"] == "PARTIALLY_TRACEABLE"
    assert block["causation_claim"] is False
    assert isinstance(block["known_blind_zones"], list)
    assert len(block["known_blind_zones"]) > 0
    assert "blind_zone_note" in block


def test_build_epistemic_block_uncertainty_note_below_threshold() -> None:
    """uncertainty_note is added when confidence is below the threshold (0.5)."""
    from app.core.epistemic import build_epistemic_block

    block = build_epistemic_block(confidence_score=0.3, data_completeness="Sparse")
    assert "uncertainty_note" in block
    assert "inconclusive" in block["uncertainty_note"].lower()


def test_build_epistemic_block_no_uncertainty_note_above_threshold() -> None:
    """uncertainty_note is absent when confidence meets or exceeds the threshold."""
    from app.core.epistemic import build_epistemic_block

    block = build_epistemic_block(confidence_score=0.6, data_completeness="Partial")
    assert "uncertainty_note" not in block


def test_derive_data_completeness() -> None:
    from app.core.epistemic import derive_data_completeness

    assert derive_data_completeness(0.8) == "Full"
    assert derive_data_completeness(0.7) == "Full"
    assert derive_data_completeness(0.5) == "Partial"
    assert derive_data_completeness(0.4) == "Partial"
    assert derive_data_completeness(0.3) == "Sparse"
    assert derive_data_completeness(0.0) == "Sparse"


def test_known_blind_zones_listed() -> None:
    from app.core.epistemic import KNOWN_BLIND_ZONES

    assert any("501" in z for z in KNOWN_BLIND_ZONES)
    assert any("offshore" in z.lower() for z in KNOWN_BLIND_ZONES)
