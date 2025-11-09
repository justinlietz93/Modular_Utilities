"""Tests for knowledge graph domain models."""
import pytest
from knowledge_graph.domain.models import GraphNode, KnowledgeGraph, GraphEdge, VerbosityLevel


def test_graph_node_creation():
    """Test creating a graph node."""
    node = GraphNode(
        id="test-1",
        content="Test content for node",
        source_file="test.txt"
    )
    
    assert node.id == "test-1"
    assert node.content == "Test content for node"
    assert node.source_file == "test.txt"
    assert node.retrieval_count == 0


def test_graph_node_uniqueness():
    """Test calculating node uniqueness."""
    node1 = GraphNode(id="1", content="machine learning neural networks")
    node2 = GraphNode(id="2", content="deep learning algorithms")
    node3 = GraphNode(id="3", content="machine learning algorithms")
    
    all_nodes = [node1, node2, node3]
    
    uniqueness1 = node1.calculate_uniqueness(all_nodes)
    uniqueness2 = node2.calculate_uniqueness(all_nodes)
    
    # Node 1 should be more unique as "neural networks" is unique
    assert uniqueness1 > uniqueness2


def test_knowledge_graph_creation():
    """Test creating a knowledge graph."""
    graph = KnowledgeGraph(graph_id="test-graph")
    
    assert graph.graph_id == "test-graph"
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0
    assert graph.metadata is not None
    assert graph.metadata.graph_id == "test-graph"


def test_knowledge_graph_add_node():
    """Test adding nodes to graph."""
    graph = KnowledgeGraph(graph_id="test-graph")
    node = GraphNode(id="node-1", content="Test content")
    
    graph.add_node(node)
    
    assert len(graph.nodes) == 1
    assert "node-1" in graph.nodes
    assert graph.metadata.node_count == 1


def test_knowledge_graph_add_edge():
    """Test adding edges to graph."""
    graph = KnowledgeGraph(graph_id="test-graph")
    edge = GraphEdge(source_id="node-1", target_id="node-2", weight=0.8)
    
    graph.add_edge(edge)
    
    assert len(graph.edges) == 1
    assert graph.edges[0].source_id == "node-1"
    assert graph.edges[0].target_id == "node-2"
    assert graph.metadata.edge_count == 1


def test_knowledge_graph_get_neighbors():
    """Test getting neighbors in graph."""
    graph = KnowledgeGraph(graph_id="test-graph")
    
    # Add nodes
    for i in range(5):
        graph.add_node(GraphNode(id=f"node-{i}", content=f"Content {i}"))
    
    # Create a chain: 0 -> 1 -> 2 -> 3 -> 4
    graph.add_edge(GraphEdge(source_id="node-0", target_id="node-1"))
    graph.add_edge(GraphEdge(source_id="node-1", target_id="node-2"))
    graph.add_edge(GraphEdge(source_id="node-2", target_id="node-3"))
    graph.add_edge(GraphEdge(source_id="node-3", target_id="node-4"))
    
    # Test 1 hop
    neighbors_1 = graph.get_neighbors("node-0", hops=1)
    assert "node-1" in neighbors_1
    assert "node-2" not in neighbors_1
    
    # Test 2 hops
    neighbors_2 = graph.get_neighbors("node-0", hops=2)
    assert "node-1" in neighbors_2
    assert "node-2" in neighbors_2
    assert "node-3" not in neighbors_2


def test_verbosity_level():
    """Test verbosity level enum."""
    assert VerbosityLevel.OFF.value == "off"
    assert VerbosityLevel.LOW.value == "low"
    assert VerbosityLevel.MEDIUM.value == "medium"
    assert VerbosityLevel.HIGH.value == "high"
    assert VerbosityLevel.MAX.value == "max"
