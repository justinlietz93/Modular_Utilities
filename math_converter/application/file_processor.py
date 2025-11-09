"""File processing service."""
from pathlib import Path
from typing import List, Optional
import os

from ..domain.syntax_types import SyntaxType, ConversionRequest
from .converter import ConversionEngine


class FileProcessor:
    """Process files for math syntax conversion."""
    
    # File extensions that might contain math
    SUPPORTED_EXTENSIONS = {'.md', '.tex', '.txt', '.rst', '.html'}
    
    def __init__(self):
        """Initialize file processor."""
        self.engine = ConversionEngine()
    
    def discover_files(self, input_paths: List[str]) -> List[Path]:
        """
        Discover files to process.
        
        Args:
            input_paths: List of file or directory paths
            
        Returns:
            List of file paths to process
        """
        files = []
        
        if not input_paths:
            # Default: scan current directory (non-recursive)
            input_paths = ['.']
        
        for path_str in input_paths:
            path = Path(path_str)
            
            if path.is_file():
                if path.suffix in self.SUPPORTED_EXTENSIONS:
                    files.append(path)
            elif path.is_dir():
                # Non-recursive scan
                for item in path.iterdir():
                    if item.is_file() and item.suffix in self.SUPPORTED_EXTENSIONS:
                        files.append(item)
        
        return files
    
    def process_file(
        self,
        file_path: Path,
        from_syntax: SyntaxType,
        to_syntax: SyntaxType,
        output_dir: Optional[str] = None,
        in_place: bool = True
    ) -> bool:
        """
        Process a single file.
        
        Args:
            file_path: Path to the file
            from_syntax: Source syntax type
            to_syntax: Target syntax type
            output_dir: Optional output directory
            in_place: Whether to modify file in place
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read the file
            content = file_path.read_text(encoding='utf-8')
            
            # Convert the content
            converted = self.engine.convert(content, from_syntax, to_syntax)
            
            # Determine output path
            if in_place and not output_dir:
                output_path = file_path
            elif output_dir:
                output_dir_path = Path(output_dir)
                output_dir_path.mkdir(parents=True, exist_ok=True)
                output_path = output_dir_path / file_path.name
            else:
                output_path = file_path
            
            # Write the converted content
            output_path.write_text(converted, encoding='utf-8')
            
            return True
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False
    
    def process_files(self, request: ConversionRequest) -> int:
        """
        Process multiple files based on conversion request.
        
        Args:
            request: Conversion request with all parameters
            
        Returns:
            Number of files successfully processed
        """
        files = self.discover_files(request.input_paths)
        
        if not files:
            print("No eligible files found.")
            return 0
        
        print(f"Found {len(files)} file(s) to process:")
        for f in files:
            print(f"  - {f}")
        
        successful = 0
        for file_path in files:
            if self.process_file(
                file_path,
                request.from_syntax,
                request.to_syntax,
                request.output_dir,
                request.in_place
            ):
                successful += 1
                print(f"✓ Converted {file_path}")
            else:
                print(f"✗ Failed to convert {file_path}")
        
        return successful
