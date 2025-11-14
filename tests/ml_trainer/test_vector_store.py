"""Tests for vector_store module."""

import pytest
import numpy as np
import tempfile
import os

from ml_trainer.vector_store import VectorStore


@pytest.fixture
def vector_store():
    """Create a VectorStore instance."""
    # Use numpy fallback for testing (no FAISS required)
    return VectorStore(dimension=384, use_faiss=False)


def test_vector_store_initialization():
    """Test VectorStore initialization."""
    store = VectorStore(dimension=128, use_faiss=False)
    
    assert store.dimension == 128
    assert store.use_faiss == False
    assert store.embeddings is not None
    assert len(store.metadata) == 0


def test_add_vectors(vector_store):
    """Test adding vectors to the store."""
    vectors = np.random.rand(5, 384).astype('float32')
    metadata = [{'id': f'test{i}'} for i in range(5)]
    
    vector_store.add_vectors(vectors, metadata)
    
    assert vector_store.get_size() == 5
    assert len(vector_store.metadata) == 5


def test_add_vectors_mismatch():
    """Test error when vectors and metadata don't match."""
    store = VectorStore(dimension=384, use_faiss=False)
    
    vectors = np.random.rand(5, 384).astype('float32')
    metadata = [{'id': 'test1'}]  # Only 1 metadata for 5 vectors
    
    with pytest.raises(ValueError):
        store.add_vectors(vectors, metadata)


def test_search(vector_store):
    """Test vector search."""
    # Add some vectors
    vectors = np.random.rand(10, 384).astype('float32')
    metadata = [{'id': f'test{i}', 'text': f'Text {i}'} for i in range(10)]
    
    vector_store.add_vectors(vectors, metadata)
    
    # Search with a query
    query = np.random.rand(384).astype('float32')
    results = vector_store.search(query, k=3)
    
    assert len(results) == 3
    assert all(isinstance(r, tuple) for r in results)
    assert all(len(r) == 2 for r in results)  # (distance, metadata)
    
    # Check that distances are sorted (closest first for cosine similarity)
    distances = [r[0] for r in results]
    # For our numpy implementation, smaller distance = more similar (sorted ascending)
    assert distances == sorted(distances), "Results should be sorted by distance"


def test_search_with_filter(vector_store):
    """Test search with filter function."""
    vectors = np.random.rand(10, 384).astype('float32')
    metadata = [
        {'id': f'test{i}', 'category': 'A' if i < 5 else 'B'}
        for i in range(10)
    ]
    
    vector_store.add_vectors(vectors, metadata)
    
    # Search only category B
    def filter_fn(meta):
        return meta.get('category') == 'B'
    
    query = np.random.rand(384).astype('float32')
    results = vector_store.search(query, k=3, filter_fn=filter_fn)
    
    assert len(results) <= 3
    assert all(r[1]['category'] == 'B' for r in results)


def test_search_empty_store():
    """Test search on empty store."""
    store = VectorStore(dimension=384, use_faiss=False)
    
    query = np.random.rand(384).astype('float32')
    results = store.search(query, k=5)
    
    assert len(results) == 0


def test_batch_search(vector_store):
    """Test batch search."""
    # Add vectors
    vectors = np.random.rand(10, 384).astype('float32')
    metadata = [{'id': f'test{i}'} for i in range(10)]
    vector_store.add_vectors(vectors, metadata)
    
    # Batch search
    queries = np.random.rand(3, 384).astype('float32')
    results = vector_store.batch_search(queries, k=2)
    
    assert len(results) == 3  # One result list per query
    assert all(len(r) == 2 for r in results)  # k=2 results each


def test_save_and_load():
    """Test saving and loading vector store."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = VectorStore(dimension=128, use_faiss=False)
        
        # Add some data
        vectors = np.random.rand(5, 128).astype('float32')
        metadata = [{'id': f'test{i}'} for i in range(5)]
        store.add_vectors(vectors, metadata)
        
        # Save
        save_path = os.path.join(temp_dir, 'test_store')
        store.save(save_path)
        
        # Load into new store
        new_store = VectorStore(dimension=128, use_faiss=False)
        new_store.load(save_path)
        
        assert new_store.get_size() == 5
        assert len(new_store.metadata) == 5
        assert np.allclose(new_store.embeddings, store.embeddings)


def test_load_nonexistent():
    """Test loading non-existent store."""
    store = VectorStore(dimension=384, use_faiss=False)
    
    with pytest.raises(FileNotFoundError):
        store.load('/nonexistent/path')


def test_get_size(vector_store):
    """Test getting store size."""
    assert vector_store.get_size() == 0
    
    vectors = np.random.rand(7, 384).astype('float32')
    metadata = [{'id': f'test{i}'} for i in range(7)]
    vector_store.add_vectors(vectors, metadata)
    
    assert vector_store.get_size() == 7


def test_clear(vector_store):
    """Test clearing the store."""
    # Add some data
    vectors = np.random.rand(5, 384).astype('float32')
    metadata = [{'id': f'test{i}'} for i in range(5)]
    vector_store.add_vectors(vectors, metadata)
    
    assert vector_store.get_size() == 5
    
    # Clear
    vector_store.clear()
    
    assert vector_store.get_size() == 0
    assert len(vector_store.metadata) == 0
