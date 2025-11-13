"""Advanced Chunking Module for Modular Utilities.

This module provides sophisticated text chunking capabilities with structural awareness,
OCR integration, and flexible input/output options.
"""

from advanced_chunking.domain.models import (
    Chunk,
    ChunkingConfig,
    ChunkingStrategy,
    ChunkMetadata,
)
from advanced_chunking.application.chunking_service import ChunkingService

__version__ = "0.1.0"

__all__ = [
    "Chunk",
    "ChunkingConfig",
    "ChunkingStrategy",
    "ChunkMetadata",
    "ChunkingService",
]
