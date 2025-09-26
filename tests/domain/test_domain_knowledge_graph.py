import pytest

from code_crawler.domain.knowledge_graph import (
    GraphValidationError,
    KnowledgeGraph,
    KnowledgeGraphSerializer,
    KnowledgeGraphValidator,
    Node,
    NodeType,
    Relationship,
    RelationshipType,
    deterministic_node_id,
    deterministic_relationship_id,
    diff_graphs,
)


def _simple_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    run_id = deterministic_node_id(NodeType.RUN, "test")
    module_id = deterministic_node_id(NodeType.MODULE, "pkg.module")
    graph.add_node(Node(run_id, NodeType.RUN, "run", ("test",), {}))
    graph.add_node(Node(module_id, NodeType.MODULE, "pkg.module", ("ast",), {}))
    graph.add_relationship(
        Relationship(
            deterministic_relationship_id(RelationshipType.CONTAINS, run_id, module_id),
            RelationshipType.CONTAINS,
            run_id,
            module_id,
            {},
        )
    )
    return graph


def test_diff_graphs_detects_added_node() -> None:
    previous = _simple_graph()
    current = _simple_graph()
    new_node_id = deterministic_node_id(NodeType.CLASS, "pkg.module.Example")
    current.add_node(Node(new_node_id, NodeType.CLASS, "Example", ("ast",), {}))
    diff = diff_graphs(previous, current)
    assert new_node_id in diff.added_nodes


def test_validator_raises_on_orphan() -> None:
    graph = KnowledgeGraph()
    orphan_id = deterministic_node_id(NodeType.CLASS, "pkg.module.Orphan")
    graph.add_node(Node(orphan_id, NodeType.CLASS, "Orphan", ("ast",), {}))
    with pytest.raises(GraphValidationError):
        KnowledgeGraphValidator.validate(graph)


def test_serializer_round_trip_preserves_nodes() -> None:
    graph = _simple_graph()
    jsonld = KnowledgeGraphSerializer.to_jsonld(graph)
    restored = KnowledgeGraph.from_dict(jsonld)
    assert set(restored.nodes) == set(graph.nodes)
