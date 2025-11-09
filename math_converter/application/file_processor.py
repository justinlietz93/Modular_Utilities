"""File processing service."""
from pathlib import Path
from typing import List, Optional

from ..domain.syntax_types import SyntaxType, ConversionRequest
from .converter import ConversionEngine
from .pdf_extractor import PDFExtractor


class FileProcessor:
    """Process files for math syntax conversion."""
    
    # File extensions that might contain math
    SUPPORTED_EXTENSIONS = {'.md', '.tex', '.txt', '.rst', '.html'}
    
    def __init__(self):
        """Initialize file processor."""
        self.engine = ConversionEngine()
        self.pdf_extractor = PDFExtractor()
    
    def is_pdf_file(self, path: Path) -> bool:
        """Check if file is a PDF."""
        return path.suffix.lower() == '.pdf'
    
    def process_pdf_extraction(
        self,
        pdf_path: Path,
        output_path: Optional[Path] = None
    ) -> bool:
        """
        Extract math from PDF and save to file.
        
        Args:
            pdf_path: Path to PDF file
            output_path: Output file path (if None, creates based on PDF name)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.pdf_extractor.is_available():
            print("Error: PDF extraction requires PyMuPDF.")
            print("Install with: pip install pymupdf")
            return False
        
        try:
            # Extract math expressions
            print(f"Extracting math from {pdf_path}...")
            expressions = self.pdf_extractor.extract_math_from_pdf(pdf_path)
            
            # Determine output path
            if output_path is None:
                output_path = pdf_path.with_suffix('.md')
            
            # Check if file exists for append mode
            append = output_path.exists()
            
            # Save based on file extension
            if output_path.suffix.lower() == '.md':
                self.pdf_extractor.save_to_markdown(expressions, output_path, append)
            else:
                self.pdf_extractor.save_to_text(expressions, output_path, append)
            
            action = "Appended to" if append else "Created"
            print(f"✓ {action} {output_path}")
            print(f"  Extracted {len(expressions)} math expression(s)")
            
            return True
            
        except Exception as e:
            print(f"Error extracting from PDF {pdf_path}: {e}")
            return False
    
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
