"""Text extraction utilities for various file formats."""
from pathlib import Path
from typing import Optional


class PDFExtractor:
    """Extract text from PDF files."""

    def __init__(self):
        """Initialize PDF extractor."""
        try:
            import fitz  # PyMuPDF
            self.fitz = fitz
            self.available = True
        except ImportError:
            self.available = False

    def extract_text(self, file_path: Path) -> Optional[str]:
        """Extract text from a PDF file."""
        if not self.available:
            return None

        try:
            doc = self.fitz.open(file_path)
            text_parts = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)

            doc.close()
            return '\n\n'.join(text_parts)
        except Exception as e:
            print(f"Warning: Could not extract text from PDF {file_path}: {e}")
            return None


class ImageExtractor:
    """Extract text from image files using OCR."""

    def __init__(self):
        """Initialize image extractor."""
        try:
            from PIL import Image
            import pytesseract
            self.Image = Image
            self.pytesseract = pytesseract
            self.available = True
        except ImportError:
            self.available = False

    def extract_text(self, file_path: Path) -> Optional[str]:
        """Extract text from an image file using OCR."""
        if not self.available:
            return None

        try:
            image = self.Image.open(file_path)
            text = self.pytesseract.image_to_string(image)
            return text.strip() if text else None
        except Exception as e:
            print(f"Warning: Could not extract text from image {file_path}: {e}")
            return None
