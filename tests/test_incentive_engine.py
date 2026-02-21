from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# entity_resolver
# ---------------------------------------------------------------------------


def test_normalize_name_basic() -> None:
    from app.entity_resolver import normalize_name

    assert normalize_name("John Smith Jr.") == "john smith"
    assert normalize_name("  ALICE   DOE  ") == "alice doe"
    assert normalize_name("O'Brien, Patrick") == "o brien patrick"


def test_normalize_name_empty() -> None:
    from app.entity_resolver import normalize_name

    assert normalize_name("") == ""


def test_compute_confidence_exact() -> None:
    from app.entity_resolver import compute_confidence, normalize_name

    a = normalize_name("John Smith")
    b = normalize_name("John Smith")
    assert compute_confidence(a, b) == 1.0


def test_compute_confidence_partial() -> None:
    from app.entity_resolver import compute_confidence, normalize_name

    a = normalize_name("John Smith")
    b = normalize_name("John A Smith")
    score = compute_confidence(a, b)
    assert 0.0 < score < 1.0


def test_compute_confidence_no_overlap() -> None:
    from app.entity_resolver import compute_confidence

    assert compute_confidence("alice", "bob") == 0.0


def test_match_entities_resolved() -> None:
    from app.entity_resolver import match_entities

    results = match_entities("John Smith", ["John Smith"])
    assert len(results) == 1
    assert results[0].resolved is True
    assert results[0].note == ""


def test_match_entities_inconclusive() -> None:
    from app.entity_resolver import match_entities

    results = match_entities("John Smith", ["Alice Johnson"])
    assert len(results) == 1
    assert results[0].resolved is False
    assert "inconclusive" in results[0].note.lower()


def test_match_entities_ambiguous_logged(caplog: pytest.LogCaptureFixture) -> None:
    import logging

    from app.entity_resolver import match_entities

    with caplog.at_level(logging.INFO, logger="app.entity_resolver.matcher"):
        results = match_entities("John Smith", ["John Adams"], threshold=0.90)

    assert results[0].resolved is False
    assert len(caplog.records) == 1
    msg = caplog.records[0].message
    assert "Ambiguous" in msg
    assert "John Smith" in msg
    assert "John Adams" in msg


# ---------------------------------------------------------------------------
# incentive_graph
# ---------------------------------------------------------------------------

_NODE_ATTRS = dict(
    source_citation="SEC/EDGAR",
    filing_date="2024-01-01",
    transparency_tier="FULLY_TRACEABLE",
)


def test_incentive_graph_add_node() -> None:
    from app.incentive_graph import IncentiveGraph

    g = IncentiveGraph()
    g.add_node("alice", "Person", **_NODE_ATTRS)
    assert g.node_count == 1
    assert g.get_node("alice")["node_type"] == "Person"


def test_incentive_graph_invalid_node_type() -> None:
    from app.incentive_graph import IncentiveGraph

    g = IncentiveGraph()
    with pytest.raises(ValueError, match="Unknown node_type"):
        g.add_node("x", "Alien", **_NODE_ATTRS)


def test_incentive_graph_missing_required_attr() -> None:
    from app.incentive_graph import IncentiveGraph

    g = IncentiveGraph()
    with pytest.raises(ValueError, match="Missing required node attributes"):
        g.add_node("x", "Person", source_citation="SEC")


def test_incentive_graph_add_edge() -> None:
    from app.incentive_graph import IncentiveGraph

    g = IncentiveGraph()
    g.add_node("alice", "Person", **_NODE_ATTRS)
    g.add_node("acme", "Organization", **_NODE_ATTRS)
    g.add_edge("alice", "acme", "EMPLOYED_BY", **_NODE_ATTRS)
    assert g.edge_count == 1
    edges = g.get_edges("alice")
    assert edges[0]["edge_type"] == "EMPLOYED_BY"


def test_incentive_graph_invalid_edge_type() -> None:
    from app.incentive_graph import IncentiveGraph

    g = IncentiveGraph()
    g.add_node("a", "Person", **_NODE_ATTRS)
    g.add_node("b", "Organization", **_NODE_ATTRS)
    with pytest.raises(ValueError, match="Unknown edge_type"):
        g.add_edge("a", "b", "UNKNOWN_EDGE", **_NODE_ATTRS)


def test_incentive_graph_edge_missing_node() -> None:
    from app.incentive_graph import IncentiveGraph

    g = IncentiveGraph()
    g.add_node("a", "Person", **_NODE_ATTRS)
    with pytest.raises(KeyError):
        g.add_edge("a", "ghost", "OWNS", **_NODE_ATTRS)


# ---------------------------------------------------------------------------
# temporal_ledger
# ---------------------------------------------------------------------------


def test_narrative_timeline_in_window() -> None:
    from datetime import datetime

    from app.temporal_ledger import NarrativeEvent, NarrativeTimeline

    tl = NarrativeTimeline()
    tl.add_event(NarrativeEvent(datetime(2024, 1, 10), "Article A", "Reuters"))
    tl.add_event(NarrativeEvent(datetime(2024, 6, 1), "Article B", "AP"))

    result = tl.in_window(datetime(2024, 1, 1), datetime(2024, 2, 1))
    assert len(result) == 1
    assert result[0].title == "Article A"


def test_financial_timeline_ordering() -> None:
    from datetime import datetime

    from app.temporal_ledger import FinancialEvent, FinancialTimeline

    tl = FinancialTimeline()
    tl.add_event(FinancialEvent(datetime(2024, 6, 1), "donation", "E1", "FEC"))
    tl.add_event(FinancialEvent(datetime(2024, 1, 1), "board_appointment", "E2", "SEC"))

    assert tl.events[0].kind == "board_appointment"
    assert tl.events[1].kind == "donation"


def test_alignment_analyzer_observable() -> None:
    from datetime import datetime

    from app.temporal_ledger import (
        FinancialEvent,
        FinancialTimeline,
        NarrativeEvent,
        NarrativeTimeline,
        analyze_alignment,
    )

    narrative = NarrativeTimeline()
    narrative.add_event(NarrativeEvent(datetime(2024, 2, 1), "Title", "Outlet"))

    financial = FinancialTimeline()
    financial.add_event(FinancialEvent(datetime(2024, 2, 10), "donation", "E1", "FEC"))

    result = analyze_alignment(narrative, financial)
    assert result.causation_claim is False
    assert isinstance(result.observable_alignment, bool)
    assert 0.0 <= result.confidence_score <= 1.0


def test_alignment_analyzer_causation_always_false() -> None:
    from datetime import datetime

    from app.temporal_ledger import (
        FinancialEvent,
        FinancialTimeline,
        NarrativeEvent,
        NarrativeTimeline,
        analyze_alignment,
    )

    narrative = NarrativeTimeline()
    narrative.add_event(NarrativeEvent(datetime(2024, 1, 1), "T", "S"))
    financial = FinancialTimeline()
    financial.add_event(FinancialEvent(datetime(2024, 1, 2), "donation", "E1", "FEC"))

    result = analyze_alignment(narrative, financial)
    assert result.causation_claim is False
    assert result.to_dict()["causation_claim"] is False


def test_alignment_empty_timelines() -> None:
    from app.temporal_ledger import FinancialTimeline, NarrativeTimeline, analyze_alignment

    result = analyze_alignment(NarrativeTimeline(), FinancialTimeline())
    assert result.observable_alignment is False
    assert result.confidence_score == 0.0
    assert result.causation_claim is False


# ---------------------------------------------------------------------------
# transparency
# ---------------------------------------------------------------------------


def test_classify_public_company() -> None:
    from app.transparency import classify_transparency

    class E:
        entity_type = "public_company"

    assert classify_transparency(E()) == "FULLY_TRACEABLE"


def test_classify_501c4() -> None:
    from app.transparency import classify_transparency

    class E:
        entity_type = "501c4"

    assert classify_transparency(E()) == "PARTIALLY_TRACEABLE"


def test_classify_shell() -> None:
    from app.transparency import classify_transparency

    class E:
        entity_type = "shell_company"

    assert classify_transparency(E()) == "STRUCTURALLY_OPAQUE"


def test_classify_unknown_defaults_opaque() -> None:
    from app.transparency import classify_transparency

    class E:
        entity_type = "mystery_entity"

    assert classify_transparency(E()) == "STRUCTURALLY_OPAQUE"


# ---------------------------------------------------------------------------
# escrow
# ---------------------------------------------------------------------------


def test_sha256_hash_string() -> None:
    from app.escrow import sha256_hash

    h = sha256_hash("hello")
    assert len(h) == 64
    assert h == sha256_hash("hello")  # deterministic


def test_sha256_hash_dict_deterministic() -> None:
    from app.escrow import sha256_hash

    d = {"b": 2, "a": 1}
    assert sha256_hash(d) == sha256_hash({"a": 1, "b": 2})


def test_upload_to_ipfs_stub() -> None:
    from app.escrow import sha256_hash, upload_to_ipfs

    h = sha256_hash("test artifact")
    cid = upload_to_ipfs(h)
    assert cid.startswith("bafybeistub")
    assert len(cid) > len("bafybeistub")


def test_timestamp_registry(tmp_path: Path) -> None:
    from app.escrow import append_to_ledger, create_entry, sha256_hash, upload_to_ipfs

    h = sha256_hash("audit data")
    cid = upload_to_ipfs(h)
    entry = create_entry(h, cid)

    ledger_path = tmp_path / "escrow_ledger.jsonl"
    append_to_ledger(entry, ledger_path)

    import json

    lines = ledger_path.read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["hash"] == h
    assert record["ipfs_cid"] == cid
    assert "timestamp" in record


# ---------------------------------------------------------------------------
# epistemic
# ---------------------------------------------------------------------------


def test_enforce_humility_low_confidence() -> None:
    from app.epistemic import enforce_humility

    result = enforce_humility({"key": "val"}, confidence_score=0.3)
    assert result.humility_injected is True
    assert "inconclusive" in result.output["humility_statement"].lower()


def test_enforce_humility_incomplete_data() -> None:
    from app.epistemic import enforce_humility

    result = enforce_humility({}, data_complete=False)
    assert result.humility_injected is True


def test_enforce_humility_unresolved_entity() -> None:
    from app.epistemic import enforce_humility

    result = enforce_humility({}, entity_resolved=False)
    assert result.humility_injected is True


def test_enforce_humility_all_ok() -> None:
    from app.epistemic import enforce_humility

    result = enforce_humility(
        {"key": "val"}, confidence_score=0.95, data_complete=True, entity_resolved=True
    )
    assert result.humility_injected is False
    assert "humility_statement" not in result.output


# ---------------------------------------------------------------------------
# internal_audit
# ---------------------------------------------------------------------------


def test_analyze_coverage_counts() -> None:
    from app.internal_audit import analyze_coverage

    records = [
        {"political_cluster": "A", "industry_cluster": "Tech", "media_outlet": "NYT"},
        {"political_cluster": "A", "industry_cluster": "Finance", "media_outlet": "WSJ"},
        {"political_cluster": "B", "industry_cluster": "Tech", "media_outlet": "NYT"},
    ]
    report = analyze_coverage(records)
    assert report.total_audits == 3
    assert report.political_cluster_counts["A"] == 2
    assert report.industry_cluster_counts["Tech"] == 2
    assert report.media_outlet_counts["NYT"] == 2


def test_analyze_coverage_empty() -> None:
    from app.internal_audit import analyze_coverage

    report = analyze_coverage([])
    assert report.total_audits == 0
    assert report.political_cluster_counts == {}


def test_cluster_balance_balanced() -> None:
    from app.internal_audit import check_cluster_balance

    counts = {"A": 5, "B": 5, "C": 5}
    result = check_cluster_balance(counts)
    assert result.balanced is True
    assert result.warning == ""


def test_cluster_balance_imbalanced() -> None:
    from app.internal_audit import check_cluster_balance

    counts = {"A": 90, "B": 10}
    result = check_cluster_balance(counts)
    assert result.balanced is False
    assert "imbalance" in result.warning.lower()
    assert result.dominant_cluster == "A"


def test_cluster_balance_empty() -> None:
    from app.internal_audit import check_cluster_balance

    result = check_cluster_balance({})
    assert result.balanced is True
    assert result.dominant_cluster is None


# ---------------------------------------------------------------------------
# doctrine
# ---------------------------------------------------------------------------


def test_doctrine_clean_text() -> None:
    from app.doctrine import check_doctrine

    violations = check_doctrine("The entity has observable financial alignment with the fund.")
    assert violations == []


def test_doctrine_banned_phrase_corrupt() -> None:
    from app.doctrine import check_doctrine

    violations = check_doctrine("This appears to be corrupt behavior.")
    assert any(v.matched_text.lower() == "corrupt" for v in violations)


def test_doctrine_banned_phrase_conflict_of_interest() -> None:
    from app.doctrine import check_doctrine

    violations = check_doctrine("There is a clear conflict of interest here.")
    assert any("conflict of interest" in v.matched_text.lower() for v in violations)


def test_doctrine_banned_phrase_intent() -> None:
    from app.doctrine import check_doctrine

    violations = check_doctrine("The actor's intent was clear.")
    assert any("intent" in v.matched_text.lower() for v in violations)


def test_doctrine_case_insensitive() -> None:
    from app.doctrine import check_doctrine

    violations = check_doctrine("CORRUPTION was observed.")
    assert len(violations) > 0


def test_doctrine_multiple_violations() -> None:
    from app.doctrine import check_doctrine

    violations = check_doctrine("corrupt and criminal and bribery")
    assert len(violations) >= 3
