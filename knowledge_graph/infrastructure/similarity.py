"""Similarity and embedding services for semantic matching."""
import re
from typing import List, Tuple
from collections import Counter
import math

from ..domain.models import GraphNode, QueryResult


class SimilarityService:
    """Service for calculating semantic similarity between text."""
    
    def __init__(self):
        """Initialize similarity service."""
        self.stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with'
        }
    
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text into tokens."""
        # Convert to lowercase and split on non-alphanumeric characters
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        # Remove stopwords
        tokens = [t for t in tokens if t not in self.stopwords and len(t) > 2]
        return tokens
    
    def calculate_tf_idf(self, query_tokens: List[str], doc_tokens: List[str], 
                         all_docs: List[List[str]]) -> float:
        """Calculate TF-IDF based similarity score."""
        if not query_tokens or not doc_tokens:
            return 0.0
        
        # Calculate term frequency in document
        doc_counter = Counter(doc_tokens)
        query_counter = Counter(query_tokens)
        
        # Calculate document frequency across all documents
        doc_freq = Counter()
        for doc in all_docs:
            unique_terms = set(doc)
            for term in unique_terms:
                doc_freq[term] += 1
        
        num_docs = len(all_docs)
        score = 0.0
        
        # Calculate TF-IDF score
        for term in query_tokens:
            if term in doc_counter:
                # Term frequency
                tf = doc_counter[term] / len(doc_tokens)
                
                # Inverse document frequency
                df = doc_freq.get(term, 0)
                idf = math.log((num_docs + 1) / (df + 1)) if df > 0 else 0
                
                score += tf * idf
        
        return score
    
    def cosine_similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        """Calculate cosine similarity between two token lists."""
        if not tokens1 or not tokens2:
            return 0.0
        
        counter1 = Counter(tokens1)
        counter2 = Counter(tokens2)
        
        # Get all unique terms
        terms = set(counter1.keys()) | set(counter2.keys())
        
        # Calculate dot product
        dot_product = sum(counter1[term] * counter2[term] for term in terms)
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(count ** 2 for count in counter1.values()))
        mag2 = math.sqrt(sum(count ** 2 for count in counter2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def calculate_similarity(self, query: str, node: GraphNode, 
                            all_nodes: List[GraphNode]) -> float:
        """Calculate similarity between query and node."""
        query_tokens = self.preprocess_text(query)
        node_tokens = self.preprocess_text(node.content)
        all_doc_tokens = [self.preprocess_text(n.content) for n in all_nodes]
        
        # Combine TF-IDF and cosine similarity
        tfidf_score = self.calculate_tf_idf(query_tokens, node_tokens, all_doc_tokens)
        cosine_score = self.cosine_similarity(query_tokens, node_tokens)
        
        # Weighted combination (favor TF-IDF slightly)
        return 0.6 * tfidf_score + 0.4 * cosine_score
    
    def rank_nodes(self, query: str, nodes: List[GraphNode]) -> List[QueryResult]:
        """Rank nodes by similarity to query."""
        if not nodes:
            return []
        
        results = []
        for node in nodes:
            score = self.calculate_similarity(query, node, nodes)
            result = QueryResult(
                node_id=node.id,
                content=node.content,
                score=score,
                source_file=node.source_file,
                metadata=node.metadata
            )
            results.append(result)
        
        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results
    
    def calculate_edge_weight(self, node1: GraphNode, node2: GraphNode,
                             all_nodes: List[GraphNode]) -> float:
        """Calculate edge weight between two nodes based on similarity."""
        tokens1 = self.preprocess_text(node1.content)
        tokens2 = self.preprocess_text(node2.content)
        
        return self.cosine_similarity(tokens1, tokens2)
