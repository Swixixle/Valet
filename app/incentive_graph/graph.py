from __future__ import annotations

from typing import Any

import networkx as nx

# Valid node types
NODE_TYPES = {
    "Person",
    "Organization",
    "BoardRole",
    "Donation",
    "StockHolding",
    "LobbyingRecord",
    "Nonprofit",
    "ShellIndicator",
}

# Valid edge types
EDGE_TYPES = {
    "SITS_ON",
    "OWNS",
    "DONATED_TO",
    "EMPLOYED_BY",
    "FUNDS",
    "LOBBIES_FOR",
}

_REQUIRED_NODE_ATTRS = {"source_citation", "filing_date", "transparency_tier"}
_REQUIRED_EDGE_ATTRS = {"source_citation", "filing_date", "transparency_tier"}


class IncentiveGraph:
    """Directed graph of incentive relationships between public entities.

    Every node and edge must carry: source_citation, filing_date, transparency_tier.
    """

    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def add_node(self, node_id: str, node_type: str, **attrs: Any) -> None:
        """Add a node.  *node_type* must be one of NODE_TYPES."""
        if node_type not in NODE_TYPES:
            raise ValueError(f"Unknown node_type {node_type!r}. Valid: {NODE_TYPES}")
        _validate_attrs(attrs, _REQUIRED_NODE_ATTRS, "node")
        self._g.add_node(node_id, node_type=node_type, **attrs)

    def get_node(self, node_id: str) -> dict[str, Any]:
        if node_id not in self._g:
            raise KeyError(node_id)
        return dict(self._g.nodes[node_id])

    # ------------------------------------------------------------------
    # Edge operations
    # ------------------------------------------------------------------

    def add_edge(self, source: str, target: str, edge_type: str, **attrs: Any) -> None:
        """Add a directed edge.  *edge_type* must be one of EDGE_TYPES."""
        if edge_type not in EDGE_TYPES:
            raise ValueError(f"Unknown edge_type {edge_type!r}. Valid: {EDGE_TYPES}")
        if source not in self._g or target not in self._g:
            raise KeyError("Both source and target nodes must be added before adding an edge.")
        _validate_attrs(attrs, _REQUIRED_EDGE_ATTRS, "edge")
        self._g.add_edge(source, target, edge_type=edge_type, **attrs)

    def get_edges(self, source: str) -> list[dict[str, Any]]:
        return [{"target": t, **dict(data)} for t, data in self._g[source].items()]

    # ------------------------------------------------------------------
    # Graph properties
    # ------------------------------------------------------------------

    @property
    def node_count(self) -> int:
        return self._g.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self._g.number_of_edges()

    def neighbors(self, node_id: str) -> list[str]:
        return list(self._g.successors(node_id))


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _validate_attrs(attrs: dict[str, Any], required: set[str], kind: str) -> None:
    missing = required - attrs.keys()
    if missing:
        raise ValueError(f"Missing required {kind} attributes: {missing}")
