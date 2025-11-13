"""Core chunking service implementing all chunking strategies."""

from pathlib import Path
from typing import List

from advanced_chunking.domain.models import (
    Chunk,
    ChunkingConfig,
    ChunkingStrategy,
    ChunkMetadata,
)
from advanced_chunking.application.structure_detector import StructureDetector
from advanced_chunking.infrastructure.tokenizers import get_tokenizer
from advanced_chunking.infrastructure.text_processors import TextProcessor
from advanced_chunking.infrastructure.file_readers import FileReader
from advanced_chunking.infrastructure.ocr_processor import OCRProcessor


class ChunkingService:
    """Service for chunking text using various strategies."""

    def __init__(self, config: ChunkingConfig):
        """Initialize chunking service.
        
        Args:
            config: Chunking configuration
        """
        self.config = config
        self.config.validate()

        self.text_processor = TextProcessor(
            repair_mojibake=config.repair_mojibake,
            repair_ocr_artifacts=config.repair_ocr_artifacts,
            normalize_whitespace=True,
        )
        self.structure_detector = StructureDetector()
        self.tokenizer = get_tokenizer(config.tokenizer_model)
        self.file_reader = FileReader()
        self.ocr_processor = OCRProcessor() if config.enable_ocr else None

    def chunk_text(self, text: str, source_file: Path) -> List[Chunk]:
        """Chunk text according to configuration.
        
        Args:
            text: Text to chunk
            source_file: Source file path for metadata
            
        Returns:
            List of chunks
        """
        # Process text (repair, normalize)
        processed_text = self.text_processor.process(text)

        # Get structure information
        structure_info = self.structure_detector.extract_structure_info(
            processed_text
        )

        # Choose chunking strategy
        if self.config.strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentence(processed_text)
        elif self.config.strategy == ChunkingStrategy.LINE:
            chunks = self._chunk_by_line(processed_text)
        elif self.config.strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(processed_text)
        elif self.config.strategy == ChunkingStrategy.WORD_COUNT:
            chunks = self._chunk_by_word_count(processed_text)
        elif self.config.strategy == ChunkingStrategy.CHARACTER_COUNT:
            chunks = self._chunk_by_character_count(processed_text)
        elif self.config.strategy == ChunkingStrategy.TOKEN_COUNT:
            chunks = self._chunk_by_token_count(processed_text)
        else:
            raise ValueError(f"Unsupported strategy: {self.config.strategy}")

        # Apply structural preservation if needed
        if (
            self.config.preserve_code_blocks or self.config.preserve_math_expressions
        ):
            chunks = self._preserve_structures(chunks, structure_info)

        # Create Chunk objects with metadata
        return self._create_chunk_objects(chunks, source_file, structure_info)

    def chunk_file(self, file_path: Path) -> List[Chunk]:
        """Chunk content from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of chunks
        """
        # Read file content
        text = self.file_reader.read_file(file_path)

        # Apply OCR if needed and file is image-based
        if self.config.enable_ocr and self.ocr_processor:
            if file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                ocr_text = self.ocr_processor.extract_text_from_image(file_path)
                if ocr_text.strip():
                    text = ocr_text

        return self.chunk_text(text, file_path)

    def _chunk_by_sentence(self, text: str) -> List[tuple[str, int, int]]:
        """Chunk text by sentences.
        
        Returns:
            List of tuples (chunk_text, start_pos, end_pos)
        """
        sentences = self.text_processor.split_into_sentences(text)
        chunks = []
        pos = 0

        for sentence in sentences:
            start = text.find(sentence, pos)
            end = start + len(sentence)
            chunks.append((sentence, start, end))
            pos = end

        return chunks

    def _chunk_by_line(self, text: str) -> List[tuple[str, int, int]]:
        """Chunk text by lines.
        
        Returns:
            List of tuples (chunk_text, start_pos, end_pos)
        """
        lines = text.split("\n")
        chunks = []
        pos = 0

        for line in lines:
            if line.strip():  # Skip empty lines
                start = pos
                end = pos + len(line)
                chunks.append((line, start, end))
            pos += len(line) + 1  # +1 for newline

        return chunks

    def _chunk_by_paragraph(self, text: str) -> List[tuple[str, int, int]]:
        """Chunk text by paragraphs.
        
        Returns:
            List of tuples (chunk_text, start_pos, end_pos)
        """
        paragraphs = self.text_processor.split_into_paragraphs(text)
        chunks = []
        pos = 0

        for para in paragraphs:
            start = text.find(para, pos)
            end = start + len(para)
            chunks.append((para, start, end))
            pos = end

        return chunks

    def _chunk_by_word_count(self, text: str) -> List[tuple[str, int, int]]:
        """Chunk text by word count.
        
        Returns:
            List of tuples (chunk_text, start_pos, end_pos)
        """
        words = text.split()
        chunks = []
        word_count = self.config.word_count

        for i in range(0, len(words), word_count):
            chunk_words = words[i : i + word_count]
            chunk_text = " ".join(chunk_words)

            # Find position in original text
            if i == 0:
                start = 0
            else:
                # Find start of first word in chunk
                start = text.find(chunk_words[0], chunks[-1][2] if chunks else 0)

            end = start + len(chunk_text)
            chunks.append((chunk_text, start, end))

        return chunks

    def _chunk_by_character_count(self, text: str) -> List[tuple[str, int, int]]:
        """Chunk text by character count.
        
        Returns:
            List of tuples (chunk_text, start_pos, end_pos)
        """
        char_count = self.config.character_count
        chunks = []

        # Try to break at sentence boundaries when possible
        sentences = self.text_processor.split_into_sentences(text)
        current_chunk = []
        current_length = 0
        pos = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_length + sentence_len > char_count and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                start = pos
                end = start + len(chunk_text)
                chunks.append((chunk_text, start, end))

                current_chunk = [sentence]
                current_length = sentence_len
                pos = end
            else:
                current_chunk.append(sentence)
                current_length += sentence_len + 1  # +1 for space

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            start = pos
            end = start + len(chunk_text)
            chunks.append((chunk_text, start, end))

        return chunks

    def _chunk_by_token_count(self, text: str) -> List[tuple[str, int, int]]:
        """Chunk text by token count.
        
        Returns:
            List of tuples (chunk_text, start_pos, end_pos)
        """
        return self.tokenizer.split_by_token_count(
            text, self.config.token_count, overlap=0
        )

    def _preserve_structures(
        self, chunks: List[tuple[str, int, int]], structure_info: dict
    ) -> List[tuple[str, int, int]]:
        """Adjust chunks to preserve code blocks and math expressions.
        
        This is a simplified implementation - in production, you'd want
        more sophisticated logic to merge/split chunks around structures.
        
        Args:
            chunks: Initial chunks
            structure_info: Structure information from detector
            
        Returns:
            Adjusted chunks
        """
        # For now, just return chunks as-is
        # A full implementation would merge chunks that split structures
        return chunks

    def _create_chunk_objects(
        self,
        chunks: List[tuple[str, int, int]],
        source_file: Path,
        structure_info: dict,
    ) -> List[Chunk]:
        """Create Chunk objects with metadata.
        
        Args:
            chunks: List of (text, start, end) tuples
            source_file: Source file path
            structure_info: Structure information
            
        Returns:
            List of Chunk objects
        """
        chunk_objects = []

        for i, (text, start, end) in enumerate(chunks):
            # Calculate metrics
            words = len(text.split())
            chars = len(text)
            tokens = self.tokenizer.count_tokens(text)

            # Check if chunk contains structures
            contains_code = self.structure_detector.has_code_structure(text)
            contains_math = self.structure_detector.has_mathematical_content(text)

            metadata = ChunkMetadata(
                chunk_number=i + 1,
                start_position=start,
                end_position=end,
                strategy=self.config.strategy,
                source_file=source_file,
                word_count=words,
                character_count=chars,
                token_count=tokens,
                contains_code=contains_code,
                contains_math=contains_math,
            )

            chunk_objects.append(Chunk(text=text, metadata=metadata))

        return chunk_objects
