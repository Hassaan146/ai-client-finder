"""GCF — Graph Context Form. Shared context as a typed graph.

Agents read/write subgraphs and pass node IDs, not text blobs -> token savings.
Serializable to JSON for persistence in the Run row.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any

_ids = itertools.count(1)


@dataclass
class Node:
    id: str
    type: str                      # Run|Plan|Tier|Candidate|Company|Problem|Solution|Contact|Draft|Card
    data: dict[str, Any] = field(default_factory=dict)


class GCF:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: list[tuple[str, str, str]] = []   # (from, relation, to)

    def add(self, type_: str, **data: Any) -> Node:
        n = Node(id=f"{type_[:2].lower()}{next(_ids)}", type=type_, data=data)
        self.nodes[n.id] = n
        return n

    def link(self, a: Node | str, rel: str, b: Node | str) -> None:
        aid = a if isinstance(a, str) else a.id
        bid = b if isinstance(b, str) else b.id
        self.edges.append((aid, rel, bid))

    def out(self, node: Node | str, rel: str | None = None) -> list[Node]:
        nid = node if isinstance(node, str) else node.id
        return [self.nodes[b] for a, r, b in self.edges
                if a == nid and (rel is None or r == rel) and b in self.nodes]

    def by_type(self, type_: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.type == type_]

    def subgraph_text(self, node: Node, rel: str | None = None, max_chars: int = 4000) -> str:
        """Compact serialization of one node + children — what an agent actually reads."""
        lines = [f"[{node.type} {node.id}] {node.data}"]
        for child in self.out(node, rel):
            lines.append(f"  -> [{child.type} {child.id}] {child.data}")
        return "\n".join(lines)[:max_chars]

    def to_dict(self) -> dict:
        return {"nodes": [{"id": n.id, "type": n.type, "data": n.data} for n in self.nodes.values()],
                "edges": self.edges}
