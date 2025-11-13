"""
Embeddings Module

Generates sentence embeddings from conversation text using sentence-transformers.
Supports incremental embedding generation and caching for efficiency.
"""

import os
import logging
import pickle
import hashlib
from typing import List, Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates embeddings using sentence-transformers.
    Falls back to a simple TF-IDF approach if sentence-transformers is unavailable.
    """
    
    def __init__(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        cache_dir: Optional[str] = None,
        use_sentence_transformers: bool = True
    ):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of sentence-transformers model
            cache_dir: Directory to cache embeddings
            use_sentence_transformers: Whether to use sentence-transformers (requires install)
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.use_sentence_transformers = use_sentence_transformers
        self.model = None
        self.vectorizer = None
        
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model."""
        if self.use_sentence_transformers:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded sentence-transformers model: {self.model_name}")
            except ImportError:
                logger.warning(
                    "sentence-transformers not available. "
                    "Install with: pip install sentence-transformers"
                )
                self.use_sentence_transformers = False
                self._initialize_tfidf()
        else:
            self._initialize_tfidf()
    
    def _initialize_tfidf(self):
        """Initialize TF-IDF vectorizer as fallback."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=384,  # Match embedding dimension
                stop_words='english',
                ngram_range=(1, 2)
            )
            logger.info("Using TF-IDF vectorizer as fallback")
        except ImportError:
            logger.error(
                "Neither sentence-transformers nor scikit-learn available. "
                "Install one with: pip install sentence-transformers OR pip install scikit-learn"
            )
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as numpy array
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            dim = 384 if self.use_sentence_transformers else 384
            return np.zeros(dim)
        
        if self.use_sentence_transformers and self.model:
            return self.model.encode(text, convert_to_numpy=True)
        elif self.vectorizer:
            # TF-IDF fallback
            # Fit on single text if not already fitted
            try:
                vec = self.vectorizer.transform([text])
                return vec.toarray()[0]
            except:
                # Not fitted yet, fit on this text
                self.vectorizer.fit([text])
                vec = self.vectorizer.transform([text])
                return vec.toarray()[0]
        else:
            raise RuntimeError("No embedding model available")
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
            
        Returns:
            Array of embeddings with shape (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        if self.use_sentence_transformers and self.model:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            return embeddings
        elif self.vectorizer:
            # TF-IDF fallback - fit on corpus
            try:
                self.vectorizer.fit(texts)
                embeddings = self.vectorizer.transform(texts)
                return embeddings.toarray()
            except Exception as e:
                logger.error(f"Error generating TF-IDF embeddings: {e}")
                # Return zero vectors as fallback
                return np.zeros((len(texts), 384))
        else:
            raise RuntimeError("No embedding model available")
    
    def embed_conversation(
        self,
        conversation_data: Dict,
        strategy: str = 'full'
    ) -> Tuple[np.ndarray, Dict]:
        """
        Generate embedding(s) for a conversation.
        
        Args:
            conversation_data: Conversation dict with messages
            strategy: Embedding strategy - 'full', 'messages', or 'chunks'
                - full: Single embedding of all text
                - messages: Separate embedding per message
                - chunks: Chunked embeddings (for very long conversations)
                
        Returns:
            Tuple of (embeddings array, metadata dict)
        """
        messages = conversation_data.get('messages', [])
        
        if strategy == 'full':
            # Single embedding of entire conversation
            full_text = "\n".join(
                [f"{msg['author']}: {msg['text']}" for msg in messages]
            )
            embedding = self.generate_embedding(full_text)
            metadata = {
                'strategy': 'full',
                'num_embeddings': 1,
                'conv_id': conversation_data.get('id')
            }
            return np.array([embedding]), metadata
            
        elif strategy == 'messages':
            # Separate embedding per message
            texts = [
                f"{msg['author']}: {msg['text']}" for msg in messages
            ]
            embeddings = self.generate_embeddings_batch(texts, show_progress=False)
            metadata = {
                'strategy': 'messages',
                'num_embeddings': len(embeddings),
                'conv_id': conversation_data.get('id')
            }
            return embeddings, metadata
            
        elif strategy == 'chunks':
            # Chunk long conversations (every 5 messages)
            chunk_size = 5
            chunks = []
            for i in range(0, len(messages), chunk_size):
                chunk_msgs = messages[i:i+chunk_size]
                chunk_text = "\n".join(
                    [f"{msg['author']}: {msg['text']}" for msg in chunk_msgs]
                )
                chunks.append(chunk_text)
            
            embeddings = self.generate_embeddings_batch(chunks, show_progress=False)
            metadata = {
                'strategy': 'chunks',
                'num_embeddings': len(embeddings),
                'chunk_size': chunk_size,
                'conv_id': conversation_data.get('id')
            }
            return embeddings, metadata
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def cache_embedding(
        self,
        conv_id: str,
        embedding: np.ndarray,
        metadata: Dict
    ) -> str:
        """
        Cache embedding to disk.
        
        Args:
            conv_id: Conversation ID
            embedding: Embedding array
            metadata: Metadata dict
            
        Returns:
            Path to cached file
        """
        if not self.cache_dir:
            raise ValueError("cache_dir not set")
        
        cache_path = os.path.join(
            self.cache_dir,
            f"{conv_id}_embedding.pkl"
        )
        
        with open(cache_path, 'wb') as f:
            pickle.dump({
                'embedding': embedding,
                'metadata': metadata
            }, f)
        
        return cache_path
    
    def load_cached_embedding(
        self,
        conv_id: str
    ) -> Optional[Tuple[np.ndarray, Dict]]:
        """
        Load cached embedding from disk.
        
        Args:
            conv_id: Conversation ID
            
        Returns:
            Tuple of (embedding, metadata) or None if not cached
        """
        if not self.cache_dir:
            return None
        
        cache_path = os.path.join(
            self.cache_dir,
            f"{conv_id}_embedding.pkl"
        )
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            return data['embedding'], data['metadata']
        except Exception as e:
            logger.warning(f"Error loading cached embedding for {conv_id}: {e}")
            return None
    
    def get_embedding_dimension(self) -> int:
        """Get the dimensionality of embeddings."""
        if self.use_sentence_transformers and self.model:
            return self.model.get_sentence_embedding_dimension()
        else:
            return 384  # Default TF-IDF dimension


def compute_text_hash(text: str) -> str:
    """Compute SHA256 hash of text for caching."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
