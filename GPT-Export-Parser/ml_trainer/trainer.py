"""
Trainer Module

Orchestrates the initial training process for the ML memory model.
"""

import os
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime

from .data_loader import DataLoader, ConversationData
from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore
from .training_tracker import TrainingTracker

logger = logging.getLogger(__name__)


class MLMemoryTrainer:
    """Orchestrates training of the ML memory model."""
    
    def __init__(
        self,
        data_dir: str,
        model_dir: str,
        embedding_model: str = 'all-MiniLM-L6-v2',
        embedding_strategy: str = 'full',
        use_cache: bool = True
    ):
        """
        Initialize ML memory trainer.
        
        Args:
            data_dir: Directory containing pruned.json
            model_dir: Directory to save trained model artifacts
            embedding_model: Name of embedding model to use
            embedding_strategy: Strategy for embeddings ('full', 'messages', 'chunks')
            use_cache: Whether to use embedding cache
        """
        self.data_dir = data_dir
        self.model_dir = model_dir
        self.embedding_strategy = embedding_strategy
        
        # Create model directory
        os.makedirs(model_dir, exist_ok=True)
        
        # Initialize components
        self.data_loader = DataLoader(data_dir)
        
        cache_dir = os.path.join(model_dir, 'cache') if use_cache else None
        self.embedding_generator = EmbeddingGenerator(
            model_name=embedding_model,
            cache_dir=cache_dir
        )
        
        embedding_dim = self.embedding_generator.get_embedding_dimension()
        self.vector_store = VectorStore(dimension=embedding_dim)
        
        tracker_db_path = os.path.join(model_dir, 'training.db')
        self.tracker = TrainingTracker(tracker_db_path)
        
        logger.info(f"Initialized MLMemoryTrainer with {embedding_model}")
    
    def train_initial(
        self,
        max_conversations: Optional[int] = None,
        show_progress: bool = True
    ) -> Dict:
        """
        Perform initial training on all conversations.
        
        Args:
            max_conversations: Limit number of conversations (for testing)
            show_progress: Whether to show progress
            
        Returns:
            Dict with training metrics
        """
        logger.info("Starting initial training...")
        
        # Load conversations
        conversations = self.data_loader.load_all_conversations()
        
        if max_conversations:
            conversations = conversations[:max_conversations]
        
        # Start training run
        run_id = self.tracker.start_training_run(
            run_type='initial',
            num_conversations=len(conversations),
            num_new=len(conversations),
            notes=f"Initial training with {self.embedding_strategy} strategy"
        )
        
        try:
            # Process conversations
            metrics = self._process_conversations(
                conversations,
                show_progress=show_progress
            )
            
            # Save model artifacts
            self._save_model()
            
            # Record metrics
            metrics_json = json.dumps(metrics)
            self.tracker.complete_training_run(run_id, status='completed', metrics=metrics_json)
            
            logger.info(f"Initial training completed successfully")
            return metrics
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            self.tracker.complete_training_run(run_id, status='failed')
            raise
    
    def train_incremental(
        self,
        show_progress: bool = True
    ) -> Dict:
        """
        Perform incremental training on new/updated conversations.
        
        Args:
            show_progress: Whether to show progress
            
        Returns:
            Dict with training metrics
        """
        logger.info("Starting incremental training...")
        
        # Get new/updated conversations
        tracker_db_path = self.tracker.db_path
        new_convs, updated_convs = self.data_loader.get_new_or_updated_conversations(
            tracker_db_path
        )
        
        all_convs = new_convs + updated_convs
        
        if not all_convs:
            logger.info("No new or updated conversations to process")
            return {
                'num_processed': 0,
                'num_new': 0,
                'num_updated': 0
            }
        
        # Start training run
        run_id = self.tracker.start_training_run(
            run_type='incremental',
            num_conversations=len(all_convs),
            num_new=len(new_convs),
            num_updated=len(updated_convs),
            notes=f"Incremental update: {len(new_convs)} new, {len(updated_convs)} updated"
        )
        
        try:
            # Load existing model if available
            self._load_model()
            
            # Process new/updated conversations
            metrics = self._process_conversations(
                all_convs,
                show_progress=show_progress
            )
            
            # Update metrics
            metrics['num_new'] = len(new_convs)
            metrics['num_updated'] = len(updated_convs)
            
            # Save updated model
            self._save_model()
            
            # Record metrics
            metrics_json = json.dumps(metrics)
            self.tracker.complete_training_run(run_id, status='completed', metrics=metrics_json)
            
            logger.info(f"Incremental training completed successfully")
            return metrics
            
        except Exception as e:
            logger.error(f"Incremental training failed: {e}")
            self.tracker.complete_training_run(run_id, status='failed')
            raise
    
    def _process_conversations(
        self,
        conversations: List[ConversationData],
        show_progress: bool = True
    ) -> Dict:
        """
        Process conversations and add to vector store.
        
        Args:
            conversations: List of conversations to process
            show_progress: Whether to show progress
            
        Returns:
            Dict with processing metrics
        """
        processed = 0
        failed = 0
        total_embeddings = 0
        
        if show_progress:
            logger.info(f"Processing {len(conversations)} conversations...")
        
        for i, conv in enumerate(conversations):
            if show_progress and (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(conversations)} conversations")
            
            try:
                # Check cache first
                cached = self.embedding_generator.load_cached_embedding(conv.id)
                
                if cached:
                    embeddings, metadata = cached
                else:
                    # Generate embeddings
                    embeddings, metadata = self.embedding_generator.embed_conversation(
                        conv.to_dict(),
                        strategy=self.embedding_strategy
                    )
                    
                    # Cache embeddings
                    if self.embedding_generator.cache_dir:
                        self.embedding_generator.cache_embedding(
                            conv.id,
                            embeddings,
                            metadata
                        )
                
                # Add to vector store
                # Create metadata entries for each embedding
                conv_metadata = []
                for j in range(len(embeddings)):
                    meta = {
                        'conv_id': conv.id,
                        'title': conv.title,
                        'create_time': conv.create_time,
                        'update_time': conv.update_time,
                        'embedding_idx': j,
                        'strategy': self.embedding_strategy,
                        'text': conv.get_full_text()  # Store full text for retrieval
                    }
                    conv_metadata.append(meta)
                
                self.vector_store.add_vectors(embeddings, conv_metadata)
                
                # Mark as trained
                try:
                    update_ts = datetime.strptime(
                        conv.update_time,
                        '%Y-%m-%d %H:%M:%S'
                    ).timestamp()
                except (ValueError, TypeError):
                    update_ts = datetime.now().timestamp()
                
                self.tracker.mark_conversation_trained(
                    conv_id=conv.id,
                    update_time=update_ts,
                    title=conv.title,
                    embedding_strategy=self.embedding_strategy,
                    num_embeddings=len(embeddings)
                )
                
                processed += 1
                total_embeddings += len(embeddings)
                
            except Exception as e:
                logger.warning(f"Failed to process conversation {conv.id}: {e}")
                failed += 1
                continue
        
        metrics = {
            'num_processed': processed,
            'num_failed': failed,
            'total_embeddings': total_embeddings,
            'avg_embeddings_per_conv': (
                total_embeddings / processed if processed > 0 else 0
            ),
            'vector_store_size': self.vector_store.get_size()
        }
        
        return metrics
    
    def _save_model(self):
        """Save model artifacts to disk."""
        # Save vector store
        vector_store_path = os.path.join(self.model_dir, 'vector_store')
        self.vector_store.save(vector_store_path)
        
        # Save configuration
        config = {
            'embedding_model': self.embedding_generator.model_name,
            'embedding_strategy': self.embedding_strategy,
            'embedding_dimension': self.embedding_generator.get_embedding_dimension(),
            'vector_store_size': self.vector_store.get_size(),
            'saved_at': datetime.now().isoformat()
        }
        
        config_path = os.path.join(self.model_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Record checkpoint
        self.tracker.save_checkpoint(
            model_path=config_path,
            vector_store_path=vector_store_path,
            num_vectors=self.vector_store.get_size()
        )
        
        logger.info(f"Saved model artifacts to {self.model_dir}")
    
    def _load_model(self):
        """Load model artifacts from disk."""
        vector_store_path = os.path.join(self.model_dir, 'vector_store')
        config_path = os.path.join(self.model_dir, 'config.json')
        
        if not os.path.exists(config_path):
            logger.info("No existing model found")
            return
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Load vector store
        try:
            self.vector_store.load(vector_store_path)
            logger.info(f"Loaded model with {self.vector_store.get_size()} vectors")
        except FileNotFoundError:
            logger.warning("Vector store not found, starting fresh")
    
    def get_training_status(self) -> Dict:
        """
        Get current training status and statistics.
        
        Returns:
            Dict with status information
        """
        stats = self.tracker.get_stats()
        data_stats = self.data_loader.get_stats()
        
        status = {
            'training_stats': stats,
            'data_stats': data_stats,
            'model_size': self.vector_store.get_size(),
            'latest_checkpoint': self.tracker.get_latest_checkpoint()
        }
        
        return status
