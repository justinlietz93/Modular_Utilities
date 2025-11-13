"""
Retrieval Module

RAG-based retrieval logic for finding relevant conversation context.
"""

import logging
from typing import List, Dict, Optional, Tuple
import numpy as np

from .vector_store import VectorStore
from .embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class ConversationRetriever:
    """Retrieves relevant conversation context using RAG approach."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_generator: EmbeddingGenerator,
        default_k: int = 5
    ):
        """
        Initialize retriever.
        
        Args:
            vector_store: Vector store containing conversation embeddings
            embedding_generator: Generator for query embeddings
            default_k: Default number of results to retrieve
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.default_k = default_k
    
    def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        filter_fn: Optional[callable] = None,
        return_scores: bool = False
    ) -> List[Dict]:
        """
        Retrieve relevant conversations for a query.
        
        Args:
            query: Query text
            k: Number of results (uses default_k if None)
            filter_fn: Optional filter function for metadata
            return_scores: Whether to include similarity scores
            
        Returns:
            List of metadata dicts with conversation info
        """
        if k is None:
            k = self.default_k
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding,
            k=k,
            filter_fn=filter_fn
        )
        
        # Format results
        retrieved = []
        for distance, metadata in results:
            result = metadata.copy()
            if return_scores:
                # Convert distance to similarity score
                result['similarity_score'] = 1.0 / (1.0 + distance)
                result['distance'] = distance
            retrieved.append(result)
        
        logger.info(f"Retrieved {len(retrieved)} results for query")
        return retrieved
    
    def retrieve_by_date_range(
        self,
        query: str,
        start_date: str,
        end_date: Optional[str] = None,
        k: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve conversations within a date range.
        
        Args:
            query: Query text
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), optional
            k: Number of results
            
        Returns:
            List of metadata dicts
        """
        from datetime import datetime
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
        
        def date_filter(metadata: Dict) -> bool:
            """Filter by date range."""
            update_time = metadata.get('update_time', '')
            try:
                conv_dt = datetime.strptime(update_time, '%Y-%m-%d %H:%M:%S')
                if end_dt:
                    return start_dt <= conv_dt <= end_dt
                else:
                    return conv_dt >= start_dt
            except (ValueError, TypeError):
                return False
        
        return self.retrieve(query, k=k, filter_fn=date_filter)
    
    def retrieve_by_conversation_id(
        self,
        conv_id: str
    ) -> Optional[Dict]:
        """
        Retrieve metadata for a specific conversation.
        
        Args:
            conv_id: Conversation ID
            
        Returns:
            Metadata dict or None
        """
        # Search all metadata for matching conv_id
        for meta in self.vector_store.metadata:
            if meta.get('conv_id') == conv_id:
                return meta
        return None
    
    def retrieve_similar_conversations(
        self,
        reference_conv_id: str,
        k: Optional[int] = None,
        exclude_self: bool = True
    ) -> List[Dict]:
        """
        Find conversations similar to a reference conversation.
        
        Args:
            reference_conv_id: ID of reference conversation
            k: Number of results
            exclude_self: Whether to exclude the reference conversation
            
        Returns:
            List of similar conversation metadata
        """
        # Find reference conversation embedding
        ref_meta = self.retrieve_by_conversation_id(reference_conv_id)
        if not ref_meta:
            logger.warning(f"Reference conversation {reference_conv_id} not found")
            return []
        
        # Get embedding index
        ref_idx = None
        for i, meta in enumerate(self.vector_store.metadata):
            if meta.get('conv_id') == reference_conv_id:
                ref_idx = i
                break
        
        if ref_idx is None:
            return []
        
        # Get reference embedding
        if self.vector_store.use_faiss:
            # Reconstruct from FAISS index
            ref_embedding = self.vector_store.index.reconstruct(ref_idx)
        else:
            ref_embedding = self.vector_store.embeddings[ref_idx]
        
        # Search with filter to exclude self
        filter_fn = None
        if exclude_self:
            def exclude_filter(meta: Dict) -> bool:
                return meta.get('conv_id') != reference_conv_id
            filter_fn = exclude_filter
        
        results = self.vector_store.search(
            ref_embedding,
            k=(k or self.default_k) + (1 if not exclude_self else 0),
            filter_fn=filter_fn
        )
        
        return [meta for _, meta in results]
    
    def retrieve_by_topic(
        self,
        topic: str,
        k: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve conversations about a specific topic.
        
        Args:
            topic: Topic description
            k: Number of results
            
        Returns:
            List of conversation metadata
        """
        # Create a rich query for the topic
        query = f"conversations about {topic}"
        return self.retrieve(query, k=k)
    
    def multi_query_retrieve(
        self,
        queries: List[str],
        k_per_query: int = 3,
        deduplicate: bool = True
    ) -> List[Dict]:
        """
        Retrieve using multiple queries and combine results.
        
        Args:
            queries: List of query strings
            k_per_query: Number of results per query
            deduplicate: Whether to remove duplicate results
            
        Returns:
            Combined list of conversation metadata
        """
        all_results = []
        seen_ids = set()
        
        for query in queries:
            results = self.retrieve(query, k=k_per_query, return_scores=True)
            
            for result in results:
                conv_id = result.get('conv_id')
                if deduplicate:
                    if conv_id not in seen_ids:
                        all_results.append(result)
                        seen_ids.add(conv_id)
                else:
                    all_results.append(result)
        
        # Sort by similarity score if available
        if all_results and 'similarity_score' in all_results[0]:
            all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        logger.info(f"Multi-query retrieval: {len(all_results)} total results")
        return all_results
    
    def get_context_window(
        self,
        query: str,
        k: int = 3,
        max_tokens: int = 2000
    ) -> Tuple[List[Dict], str]:
        """
        Retrieve context and format for LLM consumption.
        
        Args:
            query: Query text
            k: Number of conversations to retrieve
            max_tokens: Approximate max tokens for context (rough estimate)
            
        Returns:
            Tuple of (metadata list, formatted context string)
        """
        results = self.retrieve(query, k=k)
        
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough estimate: 1 token ≈ 4 chars
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Untitled')
            update_time = result.get('update_time', 'Unknown')
            text = result.get('text', '')
            
            # Format context entry
            entry = f"[Conversation {i}]\nTitle: {title}\nDate: {update_time}\n{text}\n\n"
            
            if total_chars + len(entry) > max_chars:
                # Truncate if exceeding limit
                remaining = max_chars - total_chars
                if remaining > 100:  # Only add if meaningful space left
                    context_parts.append(entry[:remaining] + "...\n\n")
                break
            
            context_parts.append(entry)
            total_chars += len(entry)
        
        formatted_context = "".join(context_parts)
        return results, formatted_context
