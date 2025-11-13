"""Output formatting for chunks."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from advanced_chunking.domain.models import Chunk


class OutputFormatter:
    """Formats and writes chunk output to files."""

    def __init__(self, output_dir: Path):
        """Initialize output formatter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_per_file_json(
        self, file_chunks: Dict[Path, List[Chunk]], base_path: Optional[Path] = None
    ) -> List[Path]:
        """Write chunks to separate JSON files (one per source file).
        
        Args:
            file_chunks: Dictionary mapping source files to their chunks
            base_path: Base path for calculating relative paths
            
        Returns:
            List of created output file paths
        """
        output_files = []

        for source_file, chunks in file_chunks.items():
            # Create output filename
            if base_path:
                rel_path = source_file.relative_to(base_path)
                output_name = str(rel_path).replace("/", "_").replace("\\", "_")
            else:
                output_name = source_file.name

            output_file = self.output_dir / f"{output_name}.chunks.json"

            # Convert chunks to dictionaries
            chunk_dicts = [chunk.to_dict() for chunk in chunks]

            # Write JSON
            output_data = {
                "source_file": str(source_file),
                "chunk_count": len(chunks),
                "chunks": chunk_dicts,
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            output_files.append(output_file)

        return output_files

    def write_aggregated_json(
        self, file_chunks: Dict[Path, List[Chunk]], output_name: str = "all_chunks.json"
    ) -> Path:
        """Write all chunks to a single aggregated JSON file.
        
        Args:
            file_chunks: Dictionary mapping source files to their chunks
            output_name: Name of the output file
            
        Returns:
            Path to the created output file
        """
        output_file = self.output_dir / output_name

        # Aggregate all chunks
        aggregated_data = {
            "total_files": len(file_chunks),
            "total_chunks": sum(len(chunks) for chunks in file_chunks.values()),
            "files": [],
        }

        for source_file, chunks in file_chunks.items():
            file_data = {
                "source_file": str(source_file),
                "chunk_count": len(chunks),
                "chunks": [chunk.to_dict() for chunk in chunks],
            }
            aggregated_data["files"].append(file_data)

        # Write JSON
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(aggregated_data, f, indent=2, ensure_ascii=False)

        return output_file

    def write_text_output(
        self, file_chunks: Dict[Path, List[Chunk]], output_name: str = "chunks.txt"
    ) -> Path:
        """Write chunks to a plain text file.
        
        Args:
            file_chunks: Dictionary mapping source files to their chunks
            output_name: Name of the output file
            
        Returns:
            Path to the created output file
        """
        output_file = self.output_dir / output_name

        with open(output_file, "w", encoding="utf-8") as f:
            for source_file, chunks in file_chunks.items():
                f.write(f"{'=' * 80}\n")
                f.write(f"Source: {source_file}\n")
                f.write(f"Chunks: {len(chunks)}\n")
                f.write(f"{'=' * 80}\n\n")

                for chunk in chunks:
                    f.write(f"--- Chunk {chunk.metadata.chunk_number} ---\n")
                    f.write(f"Position: {chunk.metadata.start_position}-{chunk.metadata.end_position}\n")
                    f.write(f"Words: {chunk.metadata.word_count}, ")
                    f.write(f"Chars: {chunk.metadata.character_count}, ")
                    f.write(f"Tokens: {chunk.metadata.token_count}\n")
                    if chunk.metadata.contains_code:
                        f.write("Contains: Code\n")
                    if chunk.metadata.contains_math:
                        f.write("Contains: Math\n")
                    f.write("\n")
                    f.write(chunk.text)
                    f.write("\n\n")

        return output_file
