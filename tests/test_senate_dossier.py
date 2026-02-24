
import os
import pytest
from fastapi.testclient import TestClient
from app.api.server import app

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures/senate-data"))
client = TestClient(app)

# Reset SenateContext singleton before and after each test
@pytest.fixture(autouse=True)
def reset_senate_singleton():
    from app.core.senate_context import SenateContext
    SenateContext._instance = None
    yield
    SenateContext._instance = None

def test_senate_vote_happy_path(monkeypatch):
    monkeypatch.setenv("SENATE_DATA_DIR", FIXTURE_DIR)
    resp = client.post("/dossier/senate-vote", json={
        "senator": "Jane Doe",
        "bill": "B1"
    })
    data = resp.json()
    assert data["ok"] is True
    assert data["vote"] == "YEA"
    assert data["senator"]["name"] == "Jane Doe"
    assert data["grounding"]["event_id"] == "E1"
    assert data["grounding"]["source_file"].startswith("events/")

def test_senate_vote_fail_closed(monkeypatch):
    monkeypatch.delenv("SENATE_DATA_DIR", raising=False)
    resp = client.post("/dossier/senate-vote", json={
        "senator": "Jane Doe",
        "bill": "B1"
    })
    data = resp.json()
    assert data["ok"] is False
    assert "No verified Senate record available" in data["message"]
