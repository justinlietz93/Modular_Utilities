"""
Vector Store Module

Manages FAISS vector database for efficient semantic search and retrieval.
Supports incremental updates and persistence.
"""

import os
import logging
import pickle
from typing import List, Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    """
    FAISS-based vector store for conversation embeddings.
    Falls back to simple numpy-based similarity if FAISS unavailable.
    """
    
    def __init__(
        self,
        dimension: int = 384,
        index_type: str = 'flat',
        use_faiss: bool = True
    ):
        """
        Initialize vector store.
        
        Args:
            dimension: Embedding dimension
            index_type: FAISS index type ('flat', 'ivf', 'hnsw')
            use_faiss: Whether to use FAISS (requires install)
        """
        self.dimension = dimension
        self.index_type = index_type
        self.use_faiss = use_faiss
        self.index = None
        self.metadata = []  # List of metadata dicts for each vector
        self.embeddings = None  # Fallback numpy array
        
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize FAISS index or fallback."""
        if self.use_faiss:
            try:
                import faiss
                
                if self.index_type == 'flat':
                    # Simple L2 distance index (exact search)
                    self.index = faiss.IndexFlatL2(self.dimension)
                elif self.index_type == 'ivf':
                    # Inverted file index (faster but approximate)
                    quantizer = faiss.IndexFlatL2(self.dimension)
                    nlist = 100  # number of clusters
                    self.index = faiss.IndexIVFFlat(
                        quantizer, self.dimension, nlist
                    )
                elif self.index_type == 'hnsw':
                    # Hierarchical NSW (very fast approximate search)
                    self.index = faiss.IndexHNSWFlat(self.dimension, 32)
                else:
                    raise ValueError(f"Unknown index type: {self.index_type}")
                
                logger.info(f"Initialized FAISS index: {self.index_type}")
                
            except ImportError:
                logger.warning(
                    "FAISS not available. Using numpy fallback. "
                    "Install with: pip install faiss-cpu"
                )
                self.use_faiss = False
                self.embeddings = np.array([]).reshape(0, self.dimension)
        else:
            # Numpy fallback
            self.embeddings = np.array([]).reshape(0, self.dimension)
            logger.info("Using numpy fallback for vector storage")
    
    def add_vectors(
        self,
        vectors: np.ndarray,
        metadata: List[Dict]
    ):
        """
        Add vectors to the store with associated metadata.
        
        Args:
            vectors: Array of shape (n, dimension)
            metadata: List of metadata dicts (one per vector)
        """
        if len(vectors) != len(metadata):
            raise ValueError("Number of vectors must match number of metadata entries")
        
        if len(vectors) == 0:
            return
        
        # Ensure vectors are float32 and contiguous
        vectors = np.ascontiguousarray(vectors.astype('float32'))
        
        if self.use_faiss and self.index:
            # Train IVF index if needed
            if self.index_type == 'ivf' and not self.index.is_trained:
                if len(vectors) >= 100:  # Need enough samples
                    self.index.train(vectors)
                else:
                    logger.warning("Not enough vectors to train IVF index, using flat search")
                    import faiss
                    self.index = faiss.IndexFlatL2(self.dimension)
            
            self.index.add(vectors)
            self.metadata.extend(metadata)
            logger.info(f"Added {len(vectors)} vectors to FAISS index")
        else:
            # Numpy fallback
            if self.embeddings.size == 0:
                self.embeddings = vectors
            else:
                self.embeddings = np.vstack([self.embeddings, vectors])
            self.metadata.extend(metadata)
            logger.info(f"Added {len(vectors)} vectors to numpy store")
    
    def search(
        self,
        query_vector: np.ndarray,
        k: int = 5,
        filter_fn: Optional[callable] = None
    ) -> List[Tuple[float, Dict]]:
        """
        Search for k nearest neighbors.
        
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            filter_fn: Optional filter function applied to metadata
            
        Returns:
            List of (distance, metadata) tuples
        """
        if len(self.metadata) == 0:
            return []
        
        # Ensure query is float32 and 2D
        query_vector = np.ascontiguousarray(
            query_vector.astype('float32')
        ).reshape(1, -1)
        
        if self.use_faiss and self.index:
            # FAISS search
            k_search = min(k * 2, len(self.metadata))  # Over-fetch for filtering
            distances, indices = self.index.search(query_vector, k_search)
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.metadata):
                    meta = self.metadata[idx]
                    if filter_fn is None or filter_fn(meta):
                        results.append((float(dist), meta))
                        if len(results) >= k:
                            break
            
            return results
        else:
            # Numpy fallback - compute cosine similarity
            # L2 normalize for cosine similarity
            query_norm = query_vector / (
                np.linalg.norm(query_vector, axis=1, keepdims=True) + 1e-8
            )
            embeddings_norm = self.embeddings / (
                np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-8
            )
            
            # Compute similarities
            similarities = np.dot(embeddings_norm, query_norm.T).flatten()
            
            # Get top k indices
            k_search = min(k * 2, len(similarities))
            top_indices = np.argsort(similarities)[::-1][:k_search]
            
            results = []
            for idx in top_indices:
                meta = self.metadata[idx]
                if filter_fn is None or filter_fn(meta):
                    # Convert similarity to distance (1 - similarity)
                    distance = 1.0 - similarities[idx]
                    results.append((float(distance), meta))
                    if len(results) >= k:
                        break
            
            return results
    
    def batch_search(
        self,
        query_vectors: np.ndarray,
        k: int = 5
    ) -> List[List[Tuple[float, Dict]]]:
        """
        Search for k nearest neighbors for multiple queries.
        
        Args:
            query_vectors: Array of query vectors (n_queries, dimension)
            k: Number of results per query
            
        Returns:
            List of result lists (one per query)
        """
        results = []
        for query_vec in query_vectors:
            results.append(self.search(query_vec, k=k))
        return results
    
    def save(self, filepath: str):
        """
        Save vector store to disk.
        
        Args:
            filepath: Path to save the store
        """
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        
        if self.use_faiss and self.index:
            import faiss
            # Save FAISS index
            faiss.write_index(self.index, filepath + '.faiss')
            # Save metadata separately
            with open(filepath + '.meta', 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata,
                    'dimension': self.dimension,
                    'index_type': self.index_type
                }, f)
            logger.info(f"Saved FAISS index to {filepath}")
        else:
            # Save numpy array and metadata
            with open(filepath, 'wb') as f:
                pickle.dump({
                    'embeddings': self.embeddings,
                    'metadata': self.metadata,
                    'dimension': self.dimension
                }, f)
            logger.info(f"Saved numpy store to {filepath}")
    
    def load(self, filepath: str):
        """
        Load vector store from disk.
        
        Args:
            filepath: Path to load the store from
        """
        if self.use_faiss:
            try:
                import faiss
                faiss_path = filepath + '.faiss'
                meta_path = filepath + '.meta'
                
                if os.path.exists(faiss_path) and os.path.exists(meta_path):
                    self.index = faiss.read_index(faiss_path)
                    with open(meta_path, 'rb') as f:
                        data = pickle.load(f)
                    self.metadata = data['metadata']
                    self.dimension = data['dimension']
                    self.index_type = data['index_type']
                    logger.info(f"Loaded FAISS index from {filepath}")
                    return
            except Exception as e:
                logger.warning(f"Could not load FAISS index: {e}")
        
        # Try loading as numpy store
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            self.embeddings = data['embeddings']
            self.metadata = data['metadata']
            self.dimension = data['dimension']
            self.use_faiss = False
            logger.info(f"Loaded numpy store from {filepath}")
        else:
            raise FileNotFoundError(f"Vector store not found at {filepath}")
    
    def get_size(self) -> int:
        """Get number of vectors in the store."""
        if self.use_faiss and self.index:
            return self.index.ntotal
        else:
            return len(self.embeddings) if self.embeddings is not None else 0
    
    def clear(self):
        """Clear all vectors from the store."""
        self._initialize_index()
        self.metadata = []
        logger.info("Cleared vector store")
