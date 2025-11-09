"""Tests for similarity service."""
import pytest
from knowledge_graph.infrastructure.similarity import SimilarityService
from knowledge_graph.domain.models import GraphNode


def test_preprocess_text():
    """Test text preprocessing."""
    service = SimilarityService()
    
    text = "The Machine Learning Algorithm"
    tokens = service.preprocess_text(text)
    
    # Stopwords should be removed, text should be lowercase
    assert "the" not in tokens
    assert "machine" in tokens
    assert "learning" in tokens
    assert "algorithm" in tokens


def test_cosine_similarity_identical():
    """Test cosine similarity with identical texts."""
    service = SimilarityService()
    
    tokens1 = ["machine", "learning", "neural", "networks"]
    tokens2 = ["machine", "learning", "neural", "networks"]
    
    similarity = service.cosine_similarity(tokens1, tokens2)
    
    assert similarity == pytest.approx(1.0, rel=0.01)


def test_cosine_similarity_different():
    """Test cosine similarity with different texts."""
    service = SimilarityService()
    
    tokens1 = ["machine", "learning"]
    tokens2 = ["quantum", "computing"]
    
    similarity = service.cosine_similarity(tokens1, tokens2)
    
    assert similarity == 0.0


def test_cosine_similarity_partial():
    """Test cosine similarity with partial overlap."""
    service = SimilarityService()
    
    tokens1 = ["machine", "learning", "algorithms"]
    tokens2 = ["machine", "learning", "models"]
    
    similarity = service.cosine_similarity(tokens1, tokens2)
    
    # Should have some similarity due to shared words
    assert 0 < similarity < 1


def test_rank_nodes():
    """Test ranking nodes by similarity to query."""
    service = SimilarityService()
    
    nodes = [
        GraphNode(id="1", content="Machine learning uses neural networks for pattern recognition"),
        GraphNode(id="2", content="Quantum computing leverages quantum mechanics"),
        GraphNode(id="3", content="Deep learning is a subset of machine learning"),
    ]
    
    query = "machine learning neural networks"
    results = service.rank_nodes(query, nodes)
    
    # First result should be most relevant
    assert len(results) == 3
    assert results[0].node_id in ["1", "3"]  # Both contain "machine learning"
    assert results[0].score > results[2].score


def test_calculate_edge_weight():
    """Test calculating edge weight between nodes."""
    service = SimilarityService()
    
    node1 = GraphNode(id="1", content="Machine learning algorithms")
    node2 = GraphNode(id="2", content="Machine learning models")
    node3 = GraphNode(id="3", content="Quantum computing")
    
    all_nodes = [node1, node2, node3]
    
    # Similar nodes should have higher weight
    weight_similar = service.calculate_edge_weight(node1, node2, all_nodes)
    weight_different = service.calculate_edge_weight(node1, node3, all_nodes)
    
    assert weight_similar > weight_different


def test_empty_content():
    """Test handling of empty content."""
    service = SimilarityService()
    
    node1 = GraphNode(id="1", content="")
    node2 = GraphNode(id="2", content="Machine learning")
    
    similarity = service.calculate_similarity("test query", node1, [node1, node2])
    
    assert similarity == 0.0
