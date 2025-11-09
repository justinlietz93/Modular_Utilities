"""Tests for graph service."""
import pytest
import tempfile
import shutil
from pathlib import Path

from knowledge_graph.application.graph_service import GraphService
from knowledge_graph.domain.models import KnowledgeGraph, GraphNode


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_create_graph(temp_storage):
    """Test creating a graph."""
    service = GraphService(storage_dir=temp_storage)
    
    success = service.create_graph("test-graph")
    
    assert success is True
    assert "test-graph" in service.list_graphs()


def test_create_duplicate_graph(temp_storage):
    """Test creating a graph that already exists."""
    service = GraphService(storage_dir=temp_storage)
    
    service.create_graph("test-graph")
    success = service.create_graph("test-graph")
    
    assert success is False


def test_get_graph(temp_storage):
    """Test retrieving a graph."""
    service = GraphService(storage_dir=temp_storage)
    
    service.create_graph("test-graph")
    graph = service.get_graph("test-graph")
    
    assert graph is not None
    assert graph.graph_id == "test-graph"


def test_get_last_graph(temp_storage):
    """Test retrieving the last accessed graph."""
    service = GraphService(storage_dir=temp_storage)
    
    service.create_graph("graph-1")
    service.create_graph("graph-2")
    
    # Last created should be graph-2
    graph = service.get_graph()
    
    assert graph is not None
    assert graph.graph_id == "graph-2"


def test_save_and_load_graph(temp_storage):
    """Test saving and loading a graph."""
    service = GraphService(storage_dir=temp_storage)
    
    # Create and populate graph
    graph = KnowledgeGraph(graph_id="test-graph")
    graph.add_node(GraphNode(id="node-1", content="Test content"))
    
    # Save graph
    service.save_graph(graph)
    
    # Load graph
    loaded_graph = service.get_graph("test-graph")
    
    assert loaded_graph is not None
    assert len(loaded_graph.nodes) == 1
    assert "node-1" in loaded_graph.nodes


def test_delete_graph(temp_storage):
    """Test deleting a graph."""
    service = GraphService(storage_dir=temp_storage)
    
    service.create_graph("test-graph")
    success = service.delete_graph("test-graph")
    
    assert success is True
    assert "test-graph" not in service.list_graphs()


def test_list_graphs(temp_storage):
    """Test listing all graphs."""
    service = GraphService(storage_dir=temp_storage)
    
    service.create_graph("graph-1")
    service.create_graph("graph-2")
    service.create_graph("graph-3")
    
    graphs = service.list_graphs()
    
    assert len(graphs) == 3
    assert "graph-1" in graphs
    assert "graph-2" in graphs
    assert "graph-3" in graphs


def test_dump_graph(temp_storage):
    """Test dumping a graph to file."""
    service = GraphService(storage_dir=temp_storage)
    
    # Create and populate graph
    graph = KnowledgeGraph(graph_id="test-graph")
    graph.add_node(GraphNode(id="node-1", content="Test content"))
    service.save_graph(graph)
    
    # Dump graph
    output_file = str(Path(temp_storage) / "dump.json")
    success = service.dump_graph("test-graph", output_file)
    
    assert success is True
    assert Path(output_file).exists()
