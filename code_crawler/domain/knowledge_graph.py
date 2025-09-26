"""Domain models for the repository knowledge graph."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterator, List, Set, Tuple


class NodeType(str, Enum):
    """Enumerates node classifications within the knowledge graph."""

    MODULE = "module"
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    TEST = "test"
    CONFIG = "config"
    DEPENDENCY = "dependency"
    ARTIFACT = "artifact"
    RUN = "run"
    ASSET = "asset"
    ASSET_CARD = "asset_card"


class RelationshipType(str, Enum):
    """Enumerates supported relationship semantics."""

    DECLARES = "declares"
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"
    TESTS = "tests"
    PRODUCES = "produces"
    REFERENCES = "references"
    DERIVES = "derives"
    DESCRIBES = "describes"


@dataclass(frozen=True)
class Node:
    """A single graph node."""

    identifier: str
    type: NodeType
    label: str
    provenance: Tuple[str, ...]
    attributes: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.identifier,
            "type": self.type.value,
            "label": self.label,
            "provenance": list(self.provenance),
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class Relationship:
    """A directional relationship between two nodes."""

    identifier: str
    type: RelationshipType
    source: str
    target: str
    attributes: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.identifier,
            "type": self.type.value,
            "source": self.source,
            "target": self.target,
            "attributes": self.attributes,
        }


class GraphValidationError(RuntimeError):
    """Raised when graph invariants are violated."""


@dataclass
class KnowledgeGraph:
    """In-memory representation of a repository knowledge graph."""

    nodes: Dict[str, Node] = field(default_factory=dict)
    relationships: Dict[str, Relationship] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        existing = self.nodes.get(node.identifier)
        if existing:
            merged_attributes = {**existing.attributes, **node.attributes}
            provenance = tuple(sorted(set(existing.provenance) | set(node.provenance)))
            self.nodes[node.identifier] = Node(
                identifier=node.identifier,
                type=node.type,
                label=node.label,
                provenance=provenance,
                attributes=merged_attributes,
            )
        else:
            self.nodes[node.identifier] = node

    def add_relationship(self, relationship: Relationship) -> None:
        if relationship.identifier in self.relationships:
            return
        self.relationships[relationship.identifier] = relationship

    def to_dict(self) -> Dict[str, object]:
        return {
            "nodes": [self.nodes[key].to_dict() for key in sorted(self.nodes)],
            "relationships": [
                self.relationships[key].to_dict()
                for key in sorted(self.relationships)
            ],
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "KnowledgeGraph":
        graph = cls()
        for node_data in payload.get("nodes", []):
            graph.add_node(
                Node(
                    identifier=node_data["id"],
                    type=NodeType(node_data["type"]),
                    label=node_data["label"],
                    provenance=tuple(node_data.get("provenance", [])),
                    attributes=node_data.get("attributes", {}),
                )
            )
        for rel_data in payload.get("relationships", []):
            graph.add_relationship(
                Relationship(
                    identifier=rel_data["id"],
                    type=RelationshipType(rel_data["type"]),
                    source=rel_data["source"],
                    target=rel_data["target"],
                    attributes=rel_data.get("attributes", {}),
                )
            )
        return graph

    def sorted_nodes(self) -> Iterator[Node]:
        for key in sorted(self.nodes):
            yield self.nodes[key]

    def sorted_relationships(self) -> Iterator[Relationship]:
        for key in sorted(self.relationships):
            yield self.relationships[key]


def deterministic_node_id(node_type: NodeType, reference: str) -> str:
    return f"{node_type.value}:{reference}".lower()


def deterministic_relationship_id(
    rel_type: RelationshipType, source: str, target: str
) -> str:
    return f"{rel_type.value}:{source}->{target}".lower()


class KnowledgeGraphSerializer:
    """Serialise the knowledge graph into external representations."""

    @staticmethod
    def to_graphml(graph: KnowledgeGraph) -> str:
        lines: List[str] = [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">",
            "  <graph edgedefault=\"directed\">",
        ]
        for node in graph.sorted_nodes():
            lines.append(f"    <node id=\"{node.identifier}\">")
            lines.append(f"      <data key=\"label\">{node.label}</data>")
            lines.append(f"      <data key=\"type\">{node.type.value}</data>")
            provenance = ",".join(node.provenance)
            lines.append(f"      <data key=\"provenance\">{provenance}</data>")
            for attr_key in sorted(node.attributes):
                value = node.attributes[attr_key]
                lines.append(
                    f"      <data key=\"{attr_key}\">{KnowledgeGraphSerializer._escape(value)}</data>"
                )
            lines.append("    </node>")
        for relationship in graph.sorted_relationships():
            lines.append(
                f"    <edge id=\"{relationship.identifier}\" source=\"{relationship.source}\" target=\"{relationship.target}\">"
            )
            lines.append(f"      <data key=\"type\">{relationship.type.value}</data>")
            for attr_key in sorted(relationship.attributes):
                value = relationship.attributes[attr_key]
                lines.append(
                    f"      <data key=\"{attr_key}\">{KnowledgeGraphSerializer._escape(value)}</data>"
                )
            lines.append("    </edge>")
        lines.append("  </graph>")
        lines.append("</graphml>")
        return "\n".join(lines)

    @staticmethod
    def to_jsonld(graph: KnowledgeGraph) -> Dict[str, object]:
        return {
            "@context": {
                "id": "@id",
                "type": "@type",
                "nodes": {
                    "@id": "#nodes",
                    "@container": "@list",
                },
                "relationships": {
                    "@id": "#relationships",
                    "@container": "@list",
                },
            },
            "nodes": [node.to_dict() for node in graph.sorted_nodes()],
            "relationships": [
                relationship.to_dict() for relationship in graph.sorted_relationships()
            ],
        }

    @staticmethod
    def _escape(value: object) -> str:
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@dataclass(frozen=True)
class GraphDiff:
    added_nodes: Set[str]
    removed_nodes: Set[str]
    added_relationships: Set[str]
    removed_relationships: Set[str]
    changed_nodes: Set[str]

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "added_nodes": sorted(self.added_nodes),
            "removed_nodes": sorted(self.removed_nodes),
            "added_relationships": sorted(self.added_relationships),
            "removed_relationships": sorted(self.removed_relationships),
            "changed_nodes": sorted(self.changed_nodes),
        }


def diff_graphs(previous: KnowledgeGraph, current: KnowledgeGraph) -> GraphDiff:
    prev_nodes = previous.nodes
    curr_nodes = current.nodes
    prev_rels = previous.relationships
    curr_rels = current.relationships

    added_nodes = set(curr_nodes) - set(prev_nodes)
    removed_nodes = set(prev_nodes) - set(curr_nodes)

    changed_nodes: Set[str] = set()
    for node_id in set(prev_nodes) & set(curr_nodes):
        if prev_nodes[node_id].attributes != curr_nodes[node_id].attributes or prev_nodes[
            node_id
        ].provenance != curr_nodes[node_id].provenance:
            changed_nodes.add(node_id)

    added_relationships = set(curr_rels) - set(prev_rels)
    removed_relationships = set(prev_rels) - set(curr_rels)

    return GraphDiff(
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        added_relationships=added_relationships,
        removed_relationships=removed_relationships,
        changed_nodes=changed_nodes,
    )


class KnowledgeGraphValidator:
    """Validate graph invariants (no orphans, cycles, or missing provenance)."""

    @staticmethod
    def validate(graph: KnowledgeGraph) -> None:
        missing: List[str] = []
        for relationship in graph.relationships.values():
            if relationship.source not in graph.nodes:
                missing.append(relationship.source)
            if relationship.target not in graph.nodes:
                missing.append(relationship.target)
        if missing:
            raise GraphValidationError(
                f"Relationships reference unknown nodes: {sorted(set(missing))}"
            )

        for node in graph.nodes.values():
            if not node.provenance:
                raise GraphValidationError(f"Node {node.identifier} missing provenance")

        adjacency: Dict[str, Set[str]] = {}
        for relationship in graph.relationships.values():
            if relationship.type in {RelationshipType.CONTAINS, RelationshipType.DECLARES}:
                adjacency.setdefault(relationship.source, set()).add(relationship.target)

        visited: Set[str] = set()
        stack: Set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in stack:
                raise GraphValidationError(f"Cycle detected involving {node_id}")
            if node_id in visited:
                return
            stack.add(node_id)
            for child in adjacency.get(node_id, set()):
                visit(child)
            stack.remove(node_id)
            visited.add(node_id)

        for node_id in adjacency:
            visit(node_id)

        declared_targets: Set[str] = set()
        for relationship in graph.relationships.values():
            if relationship.type == RelationshipType.DECLARES:
                declared_targets.add(relationship.target)
        orphans = [
            node_id
            for node_id in graph.nodes
            if graph.nodes[node_id].type
            not in {NodeType.RUN, NodeType.ARTIFACT, NodeType.ASSET, NodeType.ASSET_CARD}
            and node_id not in declared_targets
            and not any(
                rel.target == node_id and rel.type == RelationshipType.CONTAINS
                for rel in graph.relationships.values()
            )
        ]
        if orphans:
            raise GraphValidationError(f"Orphan nodes detected: {sorted(orphans)}")
