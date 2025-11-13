"""
ML Trainer Module for Personalized ChatGPT Memory

This module provides ML-based capabilities for building a "permanent memory" 
from ChatGPT conversation exports. It uses a RAG (Retrieval-Augmented Generation)
approach with vector embeddings for efficient, privacy-preserving local execution.

Main Components:
- data_loader: Load and parse pruned.json with incremental detection
- embeddings: Generate sentence embeddings from conversations
- vector_store: Manage FAISS vector database for semantic retrieval
- retrieval: RAG-based context retrieval
- prompt_builder: Context-aware prompt construction
- thread_detector: Identify open/unresolved threads
- trainer: Orchestrate training and fine-tuning
"""

__version__ = "0.1.0"
