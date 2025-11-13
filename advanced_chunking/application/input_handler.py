"""Input handling for files and directories."""

from pathlib import Path
from typing import Dict, List

from advanced_chunking.domain.models import Chunk, ChunkingConfig
from advanced_chunking.application.chunking_service import ChunkingService


class InputHandler:
    """Handles processing of single files and directories."""

    def __init__(self, config: ChunkingConfig):
        """Initialize input handler.
        
        Args:
            config: Chunking configuration
        """
        self.config = config
        self.chunking_service = ChunkingService(config)

    def process_file(self, file_path: Path) -> List[Chunk]:
        """Process a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of chunks from the file
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        return self.chunking_service.chunk_file(file_path)

    def process_directory(
        self, directory: Path, recursive: bool = True
    ) -> Dict[Path, List[Chunk]]:
        """Process all supported files in a directory.
        
        Args:
            directory: Path to the directory
            recursive: Whether to process subdirectories
            
        Returns:
            Dictionary mapping file paths to their chunks
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        # Get all supported files
        if recursive:
            files = self.chunking_service.file_reader.list_supported_files(directory)
        else:
            files = [
                f
                for f in directory.iterdir()
                if f.is_file()
                and self.chunking_service.file_reader.is_supported(f)
            ]

        # Process each file
        results = {}
        for file_path in files:
            try:
                chunks = self.process_file(file_path)
                results[file_path] = chunks
            except Exception as e:
                # Log error but continue processing
                print(f"Warning: Failed to process {file_path}: {e}")
                continue

        return results
