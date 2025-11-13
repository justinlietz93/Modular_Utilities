"""File reading utilities for various formats."""

from pathlib import Path


class FileReader:
    """Reads content from various file formats."""

    SUPPORTED_TEXT_EXTENSIONS = {
        ".txt",
        ".md",
        ".py",
        ".js",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".html",
        ".css",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".sh",
        ".bat",
        ".ps1",
    }

    def read_file(self, file_path: Path) -> str:
        """Read content from a file.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()

        if extension in self.SUPPORTED_TEXT_EXTENSIONS:
            return self._read_text_file(file_path)
        elif extension == ".pdf":
            return self._read_pdf_file(file_path)
        elif extension == ".docx":
            return self._read_docx_file(file_path)
        else:
            # Try to read as text anyway
            try:
                return self._read_text_file(file_path)
            except UnicodeDecodeError:
                raise ValueError(
                    f"Unsupported or binary file format: {extension}"
                ) from None

    def _read_text_file(self, file_path: Path) -> str:
        """Read a plain text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            File content
        """
        # Try UTF-8 first, fall back to other encodings
        encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        # Last resort: read as binary and decode with errors='replace'
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8", errors="replace")

    def _read_pdf_file(self, file_path: Path) -> str:
        """Read a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            import pymupdf as fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF is required for PDF support. "
                "Install with: pip install pymupdf"
            ) from None

        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        return text

    def _read_docx_file(self, file_path: Path) -> str:
        """Read a DOCX file.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Extracted text content
        """
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is required for DOCX support. "
                "Install with: pip install python-docx"
            ) from None

        doc = Document(file_path)
        paragraphs = [paragraph.text for paragraph in doc.paragraphs]
        return "\n\n".join(paragraphs)

    def is_supported(self, file_path: Path) -> bool:
        """Check if a file format is supported.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file format is supported
        """
        extension = file_path.suffix.lower()
        return extension in self.SUPPORTED_TEXT_EXTENSIONS or extension in [
            ".pdf",
            ".docx",
        ]

    def list_supported_files(self, directory: Path) -> list[Path]:
        """List all supported files in a directory recursively.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of supported file paths
        """
        supported_files = []

        for file_path in directory.rglob("*"):
            if file_path.is_file() and self.is_supported(file_path):
                supported_files.append(file_path)

        return sorted(supported_files)
