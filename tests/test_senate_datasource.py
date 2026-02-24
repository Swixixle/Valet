import os
import pytest
from app.datasources.senate import SenateDataSource, SenateDataUnavailableError

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures/senate-data"))

def test_missing_env_var_fails_closed(monkeypatch):
    monkeypatch.delenv("SENATE_DATA_DIR", raising=False)
    with pytest.raises(SenateDataUnavailableError):
        SenateDataSource().getSenatorById("S1")

def test_known_senator_and_bill_returns_event(monkeypatch):
    monkeypatch.setenv("SENATE_DATA_DIR", FIXTURE_DIR)
    ds = SenateDataSource()
    senator = ds.getSenatorById("S1")
    assert senator is not None
    assert senator["name"] == "Jane Doe"
    event = ds.getVoteByBillAndSenator("B1", "S1")
    assert event is not None
    assert event["event_id"] == "E1"
    assert event["vote"] == "YEA"
    assert event["source_file"].startswith("events/")
