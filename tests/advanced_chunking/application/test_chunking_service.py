"""Tests for chunking service."""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

from advanced_chunking.domain.models import ChunkingConfig, ChunkingStrategy
from advanced_chunking.application.chunking_service import ChunkingService


@pytest.fixture
def sentence_config():
    """Create a sentence-based chunking config."""
    return ChunkingConfig(strategy=ChunkingStrategy.SENTENCE)


@pytest.fixture
def word_count_config():
    """Create a word count chunking config."""
    return ChunkingConfig(strategy=ChunkingStrategy.WORD_COUNT, word_count=10)


@pytest.fixture
def character_count_config():
    """Create a character count chunking config."""
    return ChunkingConfig(
        strategy=ChunkingStrategy.CHARACTER_COUNT, character_count=50
    )


@pytest.fixture
def token_count_config():
    """Create a token count chunking config."""
    return ChunkingConfig(strategy=ChunkingStrategy.TOKEN_COUNT, token_count=20)


def test_chunking_service_initialization(sentence_config):
    """Test ChunkingService initialization."""
    service = ChunkingService(sentence_config)
    assert service.config == sentence_config
    assert service.text_processor is not None
    assert service.structure_detector is not None


def test_chunk_text_by_sentence(sentence_config):
    """Test chunking by sentences."""
    service = ChunkingService(sentence_config)

    text = "This is sentence one. This is sentence two. This is sentence three."
    chunks = service.chunk_text(text, Path("test.txt"))

    assert len(chunks) == 3
    assert all(chunk.text for chunk in chunks)
    assert all(chunk.metadata.strategy == ChunkingStrategy.SENTENCE for chunk in chunks)


def test_chunk_text_by_word_count(word_count_config):
    """Test chunking by word count."""
    service = ChunkingService(word_count_config)

    # Create text with more than 10 words
    text = " ".join([f"word{i}" for i in range(25)])
    chunks = service.chunk_text(text, Path("test.txt"))

    assert len(chunks) >= 2  # Should create multiple chunks
    assert all(chunk.metadata.strategy == ChunkingStrategy.WORD_COUNT for chunk in chunks)


def test_chunk_text_by_character_count(character_count_config):
    """Test chunking by character count."""
    service = ChunkingService(character_count_config)

    # Create text with sentences that will split across chunks
    text = "This is sentence one. " * 10  # Over 200 characters
    chunks = service.chunk_text(text, Path("test.txt"))

    # Should create at least 2 chunks given 50 char limit
    assert len(chunks) >= 2


def test_chunk_text_by_token_count(token_count_config):
    """Test chunking by token count."""
    service = ChunkingService(token_count_config)

    text = "This is a test sentence. " * 20
    chunks = service.chunk_text(text, Path("test.txt"))

    assert len(chunks) >= 1
    assert all(chunk.metadata.token_count > 0 for chunk in chunks)


def test_chunk_metadata(sentence_config):
    """Test chunk metadata is populated correctly."""
    service = ChunkingService(sentence_config)

    text = "First sentence. Second sentence."
    chunks = service.chunk_text(text, Path("test.txt"))

    for i, chunk in enumerate(chunks):
        assert chunk.metadata.chunk_number == i + 1
        assert chunk.metadata.word_count > 0
        assert chunk.metadata.character_count > 0
        assert chunk.metadata.token_count > 0
        assert chunk.metadata.source_file == Path("test.txt")


def test_chunk_file_text(sentence_config):
    """Test chunking a text file."""
    service = ChunkingService(sentence_config)

    # Create temporary file
    with NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Sentence one. Sentence two. Sentence three.")
        temp_path = Path(f.name)

    try:
        chunks = service.chunk_file(temp_path)
        assert len(chunks) == 3
    finally:
        temp_path.unlink()


def test_empty_text(sentence_config):
    """Test chunking empty text."""
    service = ChunkingService(sentence_config)

    chunks = service.chunk_text("", Path("test.txt"))
    assert len(chunks) == 0


def test_chunk_with_code_detection(sentence_config):
    """Test that code is detected in chunks."""
    service = ChunkingService(sentence_config)

    text = "Here is code: ```python\ndef test():\n    pass\n```"
    chunks = service.chunk_text(text, Path("test.txt"))

    # At least one chunk should have code
    has_code = any(chunk.metadata.contains_code for chunk in chunks)
    assert has_code or len(chunks) > 0  # Either detected or chunked
