"""Tests for embeddings module."""

import pytest
import numpy as np
import tempfile
import shutil

from ml_trainer.embeddings import EmbeddingGenerator, compute_text_hash


@pytest.fixture
def embedding_generator():
    """Create an EmbeddingGenerator instance."""
    # Use fallback mode for testing (no sentence-transformers required)
    return EmbeddingGenerator(use_sentence_transformers=False)


def test_compute_text_hash():
    """Test text hashing function."""
    text1 = "Hello world"
    text2 = "Hello world"
    text3 = "Different text"
    
    hash1 = compute_text_hash(text1)
    hash2 = compute_text_hash(text2)
    hash3 = compute_text_hash(text3)
    
    assert hash1 == hash2  # Same text = same hash
    assert hash1 != hash3  # Different text = different hash
    assert len(hash1) == 16  # Hash is 16 chars


def test_embedding_generator_initialization():
    """Test EmbeddingGenerator initialization."""
    gen = EmbeddingGenerator(use_sentence_transformers=False)
    
    assert gen.model_name == 'all-MiniLM-L6-v2'
    assert not gen.use_sentence_transformers
    assert gen.vectorizer is not None


def test_generate_embedding(embedding_generator):
    """Test single embedding generation."""
    text = "This is a test sentence"
    embedding = embedding_generator.generate_embedding(text)
    
    assert isinstance(embedding, np.ndarray)
    assert len(embedding) == 384  # Default dimension
    
    # Test empty text
    empty_embedding = embedding_generator.generate_embedding("")
    assert len(empty_embedding) == 384
    assert np.all(empty_embedding == 0)  # Should be zero vector


def test_generate_embeddings_batch(embedding_generator):
    """Test batch embedding generation."""
    texts = [
        "First sentence",
        "Second sentence",
        "Third sentence"
    ]
    
    embeddings = embedding_generator.generate_embeddings_batch(
        texts,
        show_progress=False
    )
    
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (3, 384)
    
    # Test empty batch
    empty_embeddings = embedding_generator.generate_embeddings_batch([])
    assert empty_embeddings.size == 0


def test_embed_conversation_full(embedding_generator):
    """Test conversation embedding with 'full' strategy."""
    conv_data = {
        'id': 'test1',
        'messages': [
            {'author': 'user', 'text': 'Hello'},
            {'author': 'ChatGPT', 'text': 'Hi there!'}
        ]
    }
    
    embeddings, metadata = embedding_generator.embed_conversation(
        conv_data,
        strategy='full'
    )
    
    assert embeddings.shape[0] == 1  # Single embedding
    assert embeddings.shape[1] == 384
    assert metadata['strategy'] == 'full'
    assert metadata['num_embeddings'] == 1
    assert metadata['conv_id'] == 'test1'


def test_embed_conversation_messages(embedding_generator):
    """Test conversation embedding with 'messages' strategy."""
    conv_data = {
        'id': 'test2',
        'messages': [
            {'author': 'user', 'text': 'Hello'},
            {'author': 'ChatGPT', 'text': 'Hi there!'},
            {'author': 'user', 'text': 'How are you?'}
        ]
    }
    
    embeddings, metadata = embedding_generator.embed_conversation(
        conv_data,
        strategy='messages'
    )
    
    assert embeddings.shape[0] == 3  # One per message
    assert embeddings.shape[1] == 384
    assert metadata['strategy'] == 'messages'
    assert metadata['num_embeddings'] == 3


def test_embed_conversation_chunks(embedding_generator):
    """Test conversation embedding with 'chunks' strategy."""
    # Create conversation with more than 5 messages
    messages = [
        {'author': 'user', 'text': f'Message {i}'}
        for i in range(10)
    ]
    
    conv_data = {
        'id': 'test3',
        'messages': messages
    }
    
    embeddings, metadata = embedding_generator.embed_conversation(
        conv_data,
        strategy='chunks'
    )
    
    assert embeddings.shape[0] == 2  # 10 messages / 5 per chunk = 2 chunks
    assert embeddings.shape[1] == 384
    assert metadata['strategy'] == 'chunks'
    assert metadata['chunk_size'] == 5


def test_cache_and_load_embedding():
    """Test embedding caching and loading."""
    with tempfile.TemporaryDirectory() as temp_dir:
        gen = EmbeddingGenerator(
            use_sentence_transformers=False,
            cache_dir=temp_dir
        )
        
        # Create and cache an embedding
        embedding = np.random.rand(384)
        metadata = {'test': 'data'}
        conv_id = 'test_conv'
        
        cache_path = gen.cache_embedding(conv_id, embedding, metadata)
        assert cache_path.endswith('_embedding.pkl')
        
        # Load cached embedding
        loaded_embedding, loaded_metadata = gen.load_cached_embedding(conv_id)
        
        assert np.allclose(loaded_embedding, embedding)
        assert loaded_metadata == metadata
        
        # Test non-existent cache
        result = gen.load_cached_embedding('nonexistent')
        assert result is None


def test_get_embedding_dimension(embedding_generator):
    """Test getting embedding dimension."""
    dim = embedding_generator.get_embedding_dimension()
    assert dim == 384


def test_invalid_strategy():
    """Test invalid embedding strategy."""
    gen = EmbeddingGenerator(use_sentence_transformers=False)
    conv_data = {
        'id': 'test',
        'messages': [{'author': 'user', 'text': 'Hello'}]
    }
    
    with pytest.raises(ValueError):
        gen.embed_conversation(conv_data, strategy='invalid_strategy')
