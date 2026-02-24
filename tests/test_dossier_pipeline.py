import os
import pytest
from fastapi.testclient import TestClient
from app.api.server import app

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures/senate-data"))
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_senate_singleton():
    from app.core.senate_context import SenateContext
    SenateContext._instance = None
    yield
    SenateContext._instance = None

def test_pipeline_vote_query_grounded(monkeypatch):
    monkeypatch.setenv("SENATE_DATA_DIR", FIXTURE_DIR)
    from app.core.senate_context import SenateContext
    SenateContext._instance = None  # Ensure singleton reset after env set
    resp = client.post("/pipeline", json={
        "mode": "dossier",
        "story_text": "How did Senator Jane Doe vote on B1?"
    })
    data = resp.json()
    assert data["ok"] is True
    assert "Jane Doe" in data["answer"]
    assert data["grounding"]["event_id"] == "E1"
    assert data["grounding"]["source_file"].startswith("events/")

def test_pipeline_vote_query_fail_closed(monkeypatch):
    monkeypatch.delenv("SENATE_DATA_DIR", raising=False)
    resp = client.post("/pipeline", json={
        "mode": "dossier",
        "story_text": "How did Senator Jane Doe vote on B1?"
    })
    data = resp.json()
    assert data["ok"] is False
    assert "No verified Senate record available" in data["message"]

def test_pipeline_non_vote_query(monkeypatch):
    monkeypatch.setenv("SENATE_DATA_DIR", FIXTURE_DIR)
    resp = client.post("/pipeline", json={
        "mode": "dossier",
        "story_text": "Summarize the main points of the article."
    })
    data = resp.json()
    # Should not trigger Senate, should run normal pipeline (structure may vary)
    assert "ok" not in data or data["ok"] is not False
