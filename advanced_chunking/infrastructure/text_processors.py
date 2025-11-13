"""Text processing utilities for cleaning and normalization."""

import re


class TextProcessor:
    """Handles text cleaning, normalization, and repair operations."""

    def __init__(
        self,
        repair_mojibake: bool = True,
        repair_ocr_artifacts: bool = True,
        normalize_whitespace: bool = True,
    ):
        """Initialize text processor.
        
        Args:
            repair_mojibake: Enable mojibake detection and repair
            repair_ocr_artifacts: Enable OCR artifact cleanup
            normalize_whitespace: Enable whitespace normalization
        """
        self.repair_mojibake = repair_mojibake
        self.repair_ocr_artifacts = repair_ocr_artifacts
        self.normalize_whitespace = normalize_whitespace

    def process(self, text: str) -> str:
        """Process text with all enabled repairs and normalizations.
        
        Args:
            text: Input text to process
            
        Returns:
            Processed text
        """
        if not text:
            return text

        processed = text

        if self.repair_mojibake:
            processed = self._repair_mojibake(processed)

        if self.repair_ocr_artifacts:
            processed = self._repair_ocr_artifacts(processed)

        if self.normalize_whitespace:
            processed = self._normalize_whitespace(processed)

        return processed

    def _repair_mojibake(self, text: str) -> str:
        """Detect and repair common mojibake patterns.
        
        Args:
            text: Text potentially containing mojibake
            
        Returns:
            Text with mojibake repaired
        """
        # Common mojibake patterns and their fixes using safe ASCII hex escapes
        replacements = [
            ("\xe2\x80\x99", "'"),  # Right single quotation mark
            ("\xe2\x80\x9c", '"'),  # Left double quotation mark
            ("\xe2\x80\x9d", '"'),  # Right double quotation mark
            ("\xe2\x80\x94", chr(0x2014)),  # Em dash
            ("\xe2\x80\x93", chr(0x2013)),  # En dash
            ("\xc3\xa9", "é"),
            ("\xc3\xa8", "è"),
            ("\xc3\xa0", "à"),
            ("\xc3\xa7", "ç"),
            ("\xc3\xb4", "ô"),
            ("\xc3\xa2", "â"),
            ("\xc3\xae", "î"),
            ("\xc3\xab", "ë"),
            ("\xc3\xaf", "ï"),
            ("\xc3\xbc", "ü"),
            ("\xc3\xb6", "ö"),
            ("\xc3\xb1", "ñ"),
        ]

        repaired = text
        for bad, good in replacements:
            repaired = repaired.replace(bad, good)

        # Try to detect and fix encoding issues
        try:
            # Check if text is actually latin-1 encoded as utf-8
            if any(ord(c) > 127 for c in repaired):
                try:
                    test = repaired.encode("latin-1").decode("utf-8")
                    # If successful and looks better, use it
                    if self._looks_better(test, repaired):
                        repaired = test
                except (UnicodeDecodeError, UnicodeEncodeError):
                    pass
        except Exception:
            pass

        return repaired

    def _looks_better(self, text1: str, text2: str) -> bool:
        """Heuristic to determine if text1 looks better than text2.
        
        Args:
            text1: First text to compare
            text2: Second text to compare
            
        Returns:
            True if text1 appears to have fewer encoding issues
        """
        # Count potentially problematic character sequences
        problems1 = len(re.findall(r"[Ã©Ã¨Ã Ã§â€]", text1))
        problems2 = len(re.findall(r"[Ã©Ã¨Ã Ã§â€]", text2))
        return problems1 < problems2

    def _repair_ocr_artifacts(self, text: str) -> str:
        """Clean up common OCR artifacts.
        
        Args:
            text: Text from OCR processing
            
        Returns:
            Cleaned text
        """
        cleaned = text

        # Remove common OCR noise patterns
        cleaned = re.sub(r"[|¦](?=\s|$)", "", cleaned)  # Stray vertical bars
        cleaned = re.sub(r"(?<=\s)[|¦]", "", cleaned)
        cleaned = re.sub(r"[~`´](?=\s|$)", "", cleaned)  # Stray accent marks
        cleaned = re.sub(r"(?<=\s)[~`´]", "", cleaned)

        # Fix common OCR character confusions
        # These patterns look for likely mistakes in context
        cleaned = re.sub(r"\b0(?=[a-z])", "o", cleaned)  # 0 -> o before lowercase
        cleaned = re.sub(r"\b1(?=[a-z]{2,})", "l", cleaned)  # 1 -> l in words
        cleaned = re.sub(r"(?<=[a-z])1(?=[a-z])", "l", cleaned)
        cleaned = re.sub(r"(?<=[a-z])0(?=[a-z])", "o", cleaned)

        # Fix spacing issues around punctuation
        cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)
        cleaned = re.sub(r"([.,;:!?])(?=[A-Za-z])", r"\1 ", cleaned)

        return cleaned

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text.
        
        Args:
            text: Text with potentially irregular whitespace
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        normalized = re.sub(r" +", " ", text)

        # Normalize line breaks
        normalized = re.sub(r"\r\n", "\n", normalized)
        normalized = re.sub(r"\r", "\n", normalized)

        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in normalized.split("\n")]
        normalized = "\n".join(lines)

        # Remove excessive blank lines (more than 2)
        normalized = re.sub(r"\n{4,}", "\n\n\n", normalized)

        return normalized.strip()

    def split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences intelligently.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Handle common abbreviations
        text = re.sub(r"\bDr\.", "Dr<DOT>", text)
        text = re.sub(r"\bMr\.", "Mr<DOT>", text)
        text = re.sub(r"\bMrs\.", "Mrs<DOT>", text)
        text = re.sub(r"\bMs\.", "Ms<DOT>", text)
        text = re.sub(r"\bet al\.", "et al<DOT>", text)
        text = re.sub(r"\be\.g\.", "e<DOT>g<DOT>", text)
        text = re.sub(r"\bi\.e\.", "i<DOT>e<DOT>", text)

        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

        # Restore abbreviations
        sentences = [s.replace("<DOT>", ".") for s in sentences]

        return [s.strip() for s in sentences if s.strip()]

    def split_into_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraphs
        """
        # Split on multiple line breaks
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def split_into_lines(self, text: str) -> list[str]:
        """Split text into lines.
        
        Args:
            text: Text to split
            
        Returns:
            List of lines
        """
        lines = text.split("\n")
        return [line.strip() for line in lines if line.strip()]
