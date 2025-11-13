"""Tokenization utilities for chunk counting."""

import re


class Tokenizer:
    """Base tokenizer for counting tokens in text."""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """Initialize tokenizer with model specification.
        
        Args:
            model: The model to use for tokenization estimation
        """
        self.model = model

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text.
        
        This is a simplified approximation. For production use,
        integrate with tiktoken or similar library.
        
        Args:
            text: The text to tokenize
            
        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token on average
        # This is a rough approximation for English text
        words = len(text.split())
        chars = len(text)
        # Average between word-based and character-based estimates
        return max(1, int((words + chars / 4) / 2))

    def split_by_token_count(
        self, text: str, max_tokens: int, overlap: int = 0
    ) -> list[tuple[str, int, int]]:
        """Split text into chunks by token count.
        
        Args:
            text: The text to split
            max_tokens: Maximum tokens per chunk
            overlap: Number of tokens to overlap between chunks
            
        Returns:
            List of tuples (chunk_text, start_pos, end_pos)
        """
        if not text:
            return []

        # Split into sentences for better boundary detection
        sentences = self._split_sentences(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        start_pos = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append((chunk_text, start_pos, start_pos + len(chunk_text)))

                # Start new chunk with overlap
                if overlap > 0:
                    # Keep last few sentences for overlap
                    overlap_tokens = 0
                    overlap_chunk = []
                    for sent in reversed(current_chunk):
                        sent_tokens = self.count_tokens(sent)
                        if overlap_tokens + sent_tokens <= overlap:
                            overlap_chunk.insert(0, sent)
                            overlap_tokens += sent_tokens
                        else:
                            break
                    current_chunk = overlap_chunk
                    current_tokens = overlap_tokens
                else:
                    current_chunk = []
                    current_tokens = 0

                start_pos = text.find(sentence, start_pos)

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append((chunk_text, start_pos, start_pos + len(chunk_text)))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences.
        
        Args:
            text: The text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting - can be enhanced with NLTK or spaCy
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]


def get_tokenizer(model: str = "gpt-3.5-turbo") -> Tokenizer:
    """Factory function to get appropriate tokenizer.
    
    Args:
        model: The model to use for tokenization
        
    Returns:
        Tokenizer instance
    """
    return Tokenizer(model)
