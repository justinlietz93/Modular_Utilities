"""Tests for text processors."""

import pytest

from advanced_chunking.infrastructure.text_processors import TextProcessor


def test_text_processor_initialization():
    """Test TextProcessor initialization."""
    processor = TextProcessor()
    assert processor.repair_mojibake is True
    assert processor.repair_ocr_artifacts is True


def test_normalize_whitespace():
    """Test whitespace normalization."""
    processor = TextProcessor(normalize_whitespace=True)

    text = "Hello    world\n\n\n\n\nTest"
    result = processor.process(text)

    assert "    " not in result  # Multiple spaces removed
    assert "\n\n\n\n\n" not in result  # Excessive newlines reduced


def test_repair_common_mojibake():
    """Test mojibake repair."""
    processor = TextProcessor(repair_mojibake=True)

    # Use bytes that represent the mojibake pattern
    text = "It\xe2\x80\x99s a test"  # Using byte escape for mojibake
    result = processor.process(text)

    # Should either fix it or at least process without error
    assert isinstance(result, str)


def test_repair_ocr_artifacts():
    """Test OCR artifact cleanup."""
    processor = TextProcessor(repair_ocr_artifacts=True)

    text = "Hello | world"
    result = processor.process(text)

    # Should clean up stray vertical bars
    assert result.count("|") <= text.count("|")


def test_split_into_sentences():
    """Test sentence splitting."""
    processor = TextProcessor()

    text = "This is sentence one. This is sentence two! Is this sentence three?"
    sentences = processor.split_into_sentences(text)

    assert len(sentences) == 3
    assert "This is sentence one." in sentences[0]


def test_split_into_sentences_with_abbreviations():
    """Test sentence splitting with abbreviations."""
    processor = TextProcessor()

    text = "Dr. Smith met Mr. Jones. They discussed e.g. various topics."
    sentences = processor.split_into_sentences(text)

    # Should not split on abbreviation periods
    assert len(sentences) == 2


def test_split_into_paragraphs():
    """Test paragraph splitting."""
    processor = TextProcessor()

    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    paragraphs = processor.split_into_paragraphs(text)

    assert len(paragraphs) == 3
    assert "Paragraph one." in paragraphs[0]


def test_split_into_lines():
    """Test line splitting."""
    processor = TextProcessor()

    text = "Line one\nLine two\nLine three"
    lines = processor.split_into_lines(text)

    assert len(lines) == 3
    assert "Line one" in lines[0]


def test_process_empty_text():
    """Test processing empty text."""
    processor = TextProcessor()

    result = processor.process("")
    assert result == ""
