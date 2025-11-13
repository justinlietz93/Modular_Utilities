"""Tests for domain models."""

import pytest
from pathlib import Path

from advanced_chunking.domain.models import (
    ChunkingStrategy,
    ChunkMetadata,
    Chunk,
    ChunkingConfig,
)


def test_chunking_strategy_enum():
    """Test ChunkingStrategy enum values."""
    assert ChunkingStrategy.SENTENCE.value == "sentence"
    assert ChunkingStrategy.LINE.value == "line"
    assert ChunkingStrategy.PARAGRAPH.value == "paragraph"
    assert ChunkingStrategy.WORD_COUNT.value == "word_count"
    assert ChunkingStrategy.CHARACTER_COUNT.value == "character_count"
    assert ChunkingStrategy.TOKEN_COUNT.value == "token_count"


def test_chunk_metadata_creation():
    """Test ChunkMetadata creation."""
    metadata = ChunkMetadata(
        chunk_number=1,
        start_position=0,
        end_position=100,
        strategy=ChunkingStrategy.SENTENCE,
        source_file=Path("test.txt"),
        word_count=20,
        character_count=100,
        token_count=25,
    )

    assert metadata.chunk_number == 1
    assert metadata.start_position == 0
    assert metadata.end_position == 100
    assert metadata.strategy == ChunkingStrategy.SENTENCE
    assert metadata.word_count == 20


def test_chunk_to_dict():
    """Test Chunk serialization to dictionary."""
    metadata = ChunkMetadata(
        chunk_number=1,
        start_position=0,
        end_position=50,
        strategy=ChunkingStrategy.SENTENCE,
        source_file=Path("test.txt"),
        word_count=10,
        character_count=50,
        token_count=12,
        contains_code=True,
        contains_math=False,
    )

    chunk = Chunk(text="This is a test chunk.", metadata=metadata)
    chunk_dict = chunk.to_dict()

    assert chunk_dict["text"] == "This is a test chunk."
    assert chunk_dict["metadata"]["chunk_number"] == 1
    assert chunk_dict["metadata"]["strategy"] == "sentence"
    assert chunk_dict["metadata"]["contains_code"] is True
    assert chunk_dict["metadata"]["contains_math"] is False


def test_chunking_config_validation_word_count():
    """Test configuration validation for word count strategy."""
    config = ChunkingConfig(
        strategy=ChunkingStrategy.WORD_COUNT, word_count=100
    )
    config.validate()  # Should not raise

    config_invalid = ChunkingConfig(strategy=ChunkingStrategy.WORD_COUNT)
    with pytest.raises(ValueError, match="word_count must be specified"):
        config_invalid.validate()


def test_chunking_config_validation_character_count():
    """Test configuration validation for character count strategy."""
    config = ChunkingConfig(
        strategy=ChunkingStrategy.CHARACTER_COUNT, character_count=500
    )
    config.validate()  # Should not raise

    config_invalid = ChunkingConfig(strategy=ChunkingStrategy.CHARACTER_COUNT)
    with pytest.raises(ValueError, match="character_count must be specified"):
        config_invalid.validate()


def test_chunking_config_validation_token_count():
    """Test configuration validation for token count strategy."""
    config = ChunkingConfig(
        strategy=ChunkingStrategy.TOKEN_COUNT, token_count=200
    )
    config.validate()  # Should not raise

    config_invalid = ChunkingConfig(strategy=ChunkingStrategy.TOKEN_COUNT)
    with pytest.raises(ValueError, match="token_count must be specified"):
        config_invalid.validate()


def test_chunking_config_validation_positive_values():
    """Test that counts must be positive."""
    config = ChunkingConfig(
        strategy=ChunkingStrategy.WORD_COUNT, word_count=-10
    )
    with pytest.raises(ValueError, match="word_count must be positive"):
        config.validate()

    config = ChunkingConfig(
        strategy=ChunkingStrategy.CHARACTER_COUNT, character_count=0
    )
    with pytest.raises(ValueError, match="character_count must be positive"):
        config.validate()
