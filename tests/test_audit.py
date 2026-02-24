import os
import pytest
from fastapi.testclient import TestClient
from app.api.server import app
from app.core.senate_context import SenateContext
from app.datasources.senate.senate_datasource import SenateDataSource
from app.audit.runner import run_vote_audit, run_dataset_audit

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures/senate-data"))
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_senate_singleton():
    SenateContext._instance = None
    yield
    SenateContext._instance = None

def test_vote_audit_verified(monkeypatch):
    monkeypatch.setenv("SENATE_DATA_DIR", FIXTURE_DIR)
    SenateContext._instance = None
    senate = SenateContext.get_instance()
    result = run_vote_audit(senate, "S1", "B1")
    assert result.status.value == "VERIFIED"
    assert any(c.get("coverage") for c in result.checks)
    assert not result.anomalies

def test_vote_audit_no_record(monkeypatch):
    monkeypatch.delenv("SENATE_DATA_DIR", raising=False)
    SenateContext._instance = None
    senate = SenateContext.get_instance()
    # Should fail-closed
    try:
        result = run_vote_audit(senate, "S1", "B1")
    except Exception:
        result = None
    assert result is None or result.status.value in ("NO_RECORD", "INVALID_DATA")

def test_vote_audit_ambiguous(monkeypatch, tmp_path):
    # Create ambiguous fixture
    data_dir = tmp_path / "senate-data"
    events_dir = data_dir / "events"
    senators_dir = data_dir / "senators"
    events_dir.mkdir(parents=True)
    senators_dir.mkdir()
    with open(senators_dir / "JaneDoe.json", "w", encoding="utf-8") as f:
        f.write('{"id": "S1", "name": "Jane Doe"}')
    # Two conflicting votes for same bill/senator
    with open(events_dir / "vote1.json", "w", encoding="utf-8") as f:
        f.write('{"event_id": "E1", "senator_id": "S1", "bill_id": "B1", "vote": "YEA", "timestamp": "2025-01-01T12:00:00Z"}')
    with open(events_dir / "vote2.json", "w", encoding="utf-8") as f:
        f.write('{"event_id": "E2", "senator_id": "S1", "bill_id": "B1", "vote": "NAY", "timestamp": "2025-01-01T12:00:00Z"}')
    monkeypatch.setenv("SENATE_DATA_DIR", str(data_dir))
    SenateContext._instance = None
    senate = SenateContext.get_instance()
    result = run_vote_audit(senate, "S1", "B1")
    assert result.status.value == "AMBIGUOUS"
    assert any(c.get("uniqueness") is False for c in result.checks)

def test_dataset_audit_conflict(monkeypatch, tmp_path):
    # Create dataset with conflict
    data_dir = tmp_path / "senate-data"
    events_dir = data_dir / "events"
    senators_dir = data_dir / "senators"
    events_dir.mkdir(parents=True)
    senators_dir.mkdir()
    with open(senators_dir / "JaneDoe.json", "w", encoding="utf-8") as f:
        f.write('{"id": "S1", "name": "Jane Doe"}')
    with open(events_dir / "vote1.json", "w", encoding="utf-8") as f:
        f.write('{"event_id": "E1", "senator_id": "S1", "bill_id": "B1", "vote": "YEA", "timestamp": "2025-01-01T12:00:00Z"}')
    with open(events_dir / "vote2.json", "w", encoding="utf-8") as f:
        f.write('{"event_id": "E2", "senator_id": "S1", "bill_id": "B1", "vote": "NAY", "timestamp": "2025-01-01T12:00:00Z"}')
    monkeypatch.setenv("SENATE_DATA_DIR", str(data_dir))
    SenateContext._instance = None
    senate = SenateContext.get_instance()
    result = run_dataset_audit(senate)
    assert result.status.value == "INVALID_DATA"
    assert any(a.get("conflict") for a in result.anomalies), result.anomalies

def test_audit_endpoint(monkeypatch):
    monkeypatch.setenv("SENATE_DATA_DIR", FIXTURE_DIR)
    SenateContext._instance = None
    resp = client.post("/audit/senate")
    data = resp.json()
    assert data["ok"] is True
    assert "audit" in data
    assert data["audit"]["status"] in ("VERIFIED", "INVALID_DATA")
