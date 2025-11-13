"""Tests for tokenizers."""

import pytest

from advanced_chunking.infrastructure.tokenizers import Tokenizer, get_tokenizer


def test_tokenizer_initialization():
    """Test tokenizer initialization."""
    tokenizer = Tokenizer()
    assert tokenizer.model == "gpt-3.5-turbo"

    tokenizer2 = Tokenizer("gpt-4")
    assert tokenizer2.model == "gpt-4"


def test_count_tokens_basic():
    """Test basic token counting."""
    tokenizer = Tokenizer()

    text = "This is a simple test."
    count = tokenizer.count_tokens(text)

    assert count > 0
    assert isinstance(count, int)


def test_count_tokens_empty():
    """Test token counting with empty text."""
    tokenizer = Tokenizer()

    count = tokenizer.count_tokens("")
    assert count >= 0


def test_split_by_token_count():
    """Test splitting text by token count."""
    tokenizer = Tokenizer()

    text = "This is a test. This is another test. And another one. And yet another."
    chunks = tokenizer.split_by_token_count(text, max_tokens=10)

    assert len(chunks) > 0
    for chunk_text, start, end in chunks:
        assert isinstance(chunk_text, str)
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert start < end


def test_split_by_token_count_with_overlap():
    """Test splitting with overlap."""
    tokenizer = Tokenizer()

    # Create longer text to ensure multiple chunks
    text = "This is sentence one. " * 10  # Long enough to split
    chunks = tokenizer.split_by_token_count(text, max_tokens=10, overlap=3)

    # Should create multiple chunks
    assert len(chunks) >= 2


def test_get_tokenizer_factory():
    """Test tokenizer factory function."""
    tokenizer = get_tokenizer()
    assert isinstance(tokenizer, Tokenizer)

    tokenizer2 = get_tokenizer("custom-model")
    assert tokenizer2.model == "custom-model"
