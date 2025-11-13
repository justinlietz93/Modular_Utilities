"""OCR processing for image-based text extraction."""

from pathlib import Path


class OCRProcessor:
    """Handles OCR operations for extracting text from images and scanned documents."""

    def __init__(self, language: str = "eng"):
        """Initialize OCR processor.
        
        Args:
            language: Language code for OCR (default: English)
        """
        self.language = language
        self._tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Check if Tesseract OCR is available.
        
        Returns:
            True if Tesseract is available
        """
        try:
            import pytesseract

            # Try to get version to verify installation
            pytesseract.get_tesseract_version()
            return True
        except (ImportError, Exception):
            return False

    def extract_text_from_image(self, image_path: Path) -> str:
        """Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text
            
        Raises:
            ImportError: If required libraries are not installed
            FileNotFoundError: If image file doesn't exist
        """
        if not self._tesseract_available:
            raise ImportError(
                "pytesseract and Pillow are required for OCR. "
                "Install with: pip install pytesseract pillow\n"
                "Also ensure Tesseract OCR is installed on your system."
            )

        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            import pytesseract
            from PIL import Image
        except ImportError as e:
            raise ImportError(
                "Required OCR libraries not available. "
                "Install with: pip install pytesseract pillow"
            ) from e

        # Open and process image
        image = Image.open(image_path)

        # Preprocess image for better OCR results
        image = self._preprocess_image(image)

        # Extract text
        text = pytesseract.image_to_string(image, lang=self.language)

        return text

    def _preprocess_image(self, image):
        """Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        from PIL import ImageEnhance

        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")

        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)

        return image

    def extract_text_from_pdf_images(self, pdf_path: Path) -> str:
        """Extract text from images within a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from all images
        """
        if not self._tesseract_available:
            raise ImportError(
                "pytesseract and Pillow are required for OCR. "
                "Install with: pip install pytesseract pillow"
            )

        try:
            import pymupdf as fitz
            import pytesseract
            from PIL import Image
        except ImportError as e:
            raise ImportError(
                "pymupdf, pytesseract, and Pillow are required. "
                "Install with: pip install pymupdf pytesseract pillow"
            ) from e

        doc = fitz.open(pdf_path)
        extracted_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Extract images from page
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Convert to PIL Image
                import io

                image = Image.open(io.BytesIO(image_bytes))

                # Preprocess and extract text
                image = self._preprocess_image(image)
                text = pytesseract.image_to_string(image, lang=self.language)

                if text.strip():
                    extracted_text.append(text)

        doc.close()

        return "\n\n".join(extracted_text)

    def is_ocr_available(self) -> bool:
        """Check if OCR functionality is available.
        
        Returns:
            True if OCR is available
        """
        return self._tesseract_available
