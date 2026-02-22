from __future__ import annotations

import pytest

from app.escrow.signing import sign_receipt, verify_receipt_signature


def test_sign_and_verify_receipt_round_trip() -> None:
    receipt = {
        "slug": "example-slug",
        "mode": "scalpel",
        "hook": "Sample hook",
        "clinical_recommendation": "Sample recommendation",
        "cta": "Sample CTA",
        "final_line": "Sample line",
    }

    signed = sign_receipt(receipt, key="abc123")
    assert "signature" in signed
    assert signed["signature"]["algorithm"] == "hmac-sha256"
    assert verify_receipt_signature(signed, key="abc123")


def test_verify_receipt_signature_detects_tampering() -> None:
    receipt = {
        "slug": "example-slug",
        "mode": "scalpel",
        "hook": "Sample hook",
        "clinical_recommendation": "Original recommendation",
        "cta": "Sample CTA",
        "final_line": "Sample line",
    }

    signed = sign_receipt(receipt, key="abc123")
    signed["clinical_recommendation"] = "Tampered recommendation"

    assert not verify_receipt_signature(signed, key="abc123")


def test_sign_receipt_raises_when_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RECEIPT_SIGNING_KEY", raising=False)
    receipt = {"slug": "x", "mode": "scalpel"}

    with pytest.raises(OSError, match="RECEIPT_SIGNING_KEY is not set"):
        sign_receipt(receipt)
