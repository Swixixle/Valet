from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _receipt_signing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RECEIPT_SIGNING_KEY", "test-receipt-signing-key")
