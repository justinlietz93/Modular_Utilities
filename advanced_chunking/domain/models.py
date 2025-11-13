"""Domain models for the advanced chunking module."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ChunkingStrategy(Enum):
    """Supported text chunking strategies."""

    SENTENCE = "sentence"
    LINE = "line"
    PARAGRAPH = "paragraph"
    WORD_COUNT = "word_count"
    CHARACTER_COUNT = "character_count"
    TOKEN_COUNT = "token_count"


@dataclass
class ChunkMetadata:
    """Metadata associated with a text chunk."""

    chunk_number: int
    start_position: int
    end_position: int
    strategy: ChunkingStrategy
    source_file: Path
    word_count: int = 0
    character_count: int = 0
    token_count: int = 0
    contains_code: bool = False
    contains_math: bool = False
    additional_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """Represents a text chunk with its content and metadata."""

    text: str
    metadata: ChunkMetadata

    def to_dict(self) -> dict[str, Any]:
        """Convert chunk to dictionary format for JSON serialization."""
        return {
            "text": self.text,
            "metadata": {
                "chunk_number": self.metadata.chunk_number,
                "start_position": self.metadata.start_position,
                "end_position": self.metadata.end_position,
                "strategy": self.metadata.strategy.value,
                "source_file": str(self.metadata.source_file),
                "word_count": self.metadata.word_count,
                "character_count": self.metadata.character_count,
                "token_count": self.metadata.token_count,
                "contains_code": self.metadata.contains_code,
                "contains_math": self.metadata.contains_math,
                **self.metadata.additional_metadata,
            },
        }


@dataclass
class ChunkingConfig:
    """Configuration for chunking operations."""

    strategy: ChunkingStrategy
    # Strategy-specific parameters
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    token_count: Optional[int] = None
    tokenizer_model: str = "gpt-3.5-turbo"
    # Structural awareness
    preserve_code_blocks: bool = True
    preserve_math_expressions: bool = True
    # OCR and text repair
    enable_ocr: bool = False
    repair_ocr_artifacts: bool = True
    repair_mojibake: bool = True
    # Output options
    include_metadata: bool = True
    output_format: str = "json"  # json or text

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.strategy == ChunkingStrategy.WORD_COUNT and self.word_count is None:
            raise ValueError("word_count must be specified for WORD_COUNT strategy")
        if (
            self.strategy == ChunkingStrategy.CHARACTER_COUNT
            and self.character_count is None
        ):
            raise ValueError(
                "character_count must be specified for CHARACTER_COUNT strategy"
            )
        if self.strategy == ChunkingStrategy.TOKEN_COUNT and self.token_count is None:
            raise ValueError("token_count must be specified for TOKEN_COUNT strategy")

        if self.word_count is not None and self.word_count <= 0:
            raise ValueError("word_count must be positive")
        if self.character_count is not None and self.character_count <= 0:
            raise ValueError("character_count must be positive")
        if self.token_count is not None and self.token_count <= 0:
            raise ValueError("token_count must be positive")
