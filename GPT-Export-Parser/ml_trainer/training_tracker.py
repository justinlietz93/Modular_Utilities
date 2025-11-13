"""
Training Tracker Module

Tracks which conversations have been processed and maintains training state
for incremental fine-tuning.
"""

import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TrainingTracker:
    """Tracks processed conversations and training state."""
    
    def __init__(self, db_path: str):
        """
        Initialize training tracker.
        
        Args:
            db_path: Path to SQLite database for tracking
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            
            # Table for tracked conversations
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS trained_conversations (
                    conv_id TEXT PRIMARY KEY,
                    update_time REAL,
                    title TEXT,
                    embedding_strategy TEXT,
                    num_embeddings INTEGER,
                    trained_at REAL,
                    model_version TEXT
                )
                """
            )
            
            # Table for training runs
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS training_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_type TEXT,
                    started_at REAL,
                    completed_at REAL,
                    num_conversations INTEGER,
                    num_new INTEGER,
                    num_updated INTEGER,
                    status TEXT,
                    metrics TEXT,
                    notes TEXT
                )
                """
            )
            
            # Table for model checkpoints
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS model_checkpoints (
                    checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at REAL,
                    model_path TEXT,
                    vector_store_path TEXT,
                    num_vectors INTEGER,
                    model_version TEXT,
                    description TEXT
                )
                """
            )
            
            conn.commit()
        finally:
            conn.close()
        
        logger.info(f"Initialized training tracker database at {self.db_path}")
    
    def mark_conversation_trained(
        self,
        conv_id: str,
        update_time: float,
        title: str,
        embedding_strategy: str,
        num_embeddings: int,
        model_version: str = '0.1.0'
    ):
        """
        Mark a conversation as trained.
        
        Args:
            conv_id: Conversation ID
            update_time: Update timestamp
            title: Conversation title
            embedding_strategy: Strategy used ('full', 'messages', 'chunks')
            num_embeddings: Number of embeddings generated
            model_version: Model version identifier
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO trained_conversations 
                (conv_id, update_time, title, embedding_strategy, num_embeddings, 
                 trained_at, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(conv_id) DO UPDATE SET
                    update_time=excluded.update_time,
                    title=excluded.title,
                    embedding_strategy=excluded.embedding_strategy,
                    num_embeddings=excluded.num_embeddings,
                    trained_at=excluded.trained_at,
                    model_version=excluded.model_version
                """,
                (
                    conv_id,
                    update_time,
                    title,
                    embedding_strategy,
                    num_embeddings,
                    datetime.now().timestamp(),
                    model_version
                )
            )
            conn.commit()
        finally:
            conn.close()
    
    def is_conversation_trained(self, conv_id: str) -> bool:
        """
        Check if a conversation has been trained.
        
        Args:
            conv_id: Conversation ID
            
        Returns:
            True if trained, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT conv_id FROM trained_conversations WHERE conv_id = ?",
                (conv_id,)
            )
            return cur.fetchone() is not None
        finally:
            conn.close()
    
    def get_trained_conversation_info(self, conv_id: str) -> Optional[Dict]:
        """
        Get training info for a conversation.
        
        Args:
            conv_id: Conversation ID
            
        Returns:
            Dict with training info or None
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT conv_id, update_time, title, embedding_strategy, 
                       num_embeddings, trained_at, model_version
                FROM trained_conversations WHERE conv_id = ?
                """,
                (conv_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                'conv_id': row[0],
                'update_time': row[1],
                'title': row[2],
                'embedding_strategy': row[3],
                'num_embeddings': row[4],
                'trained_at': row[5],
                'model_version': row[6]
            }
        finally:
            conn.close()
    
    def start_training_run(
        self,
        run_type: str,
        num_conversations: int,
        num_new: int = 0,
        num_updated: int = 0,
        notes: Optional[str] = None
    ) -> int:
        """
        Record the start of a training run.
        
        Args:
            run_type: Type of run ('initial', 'incremental')
            num_conversations: Total conversations to process
            num_new: Number of new conversations
            num_updated: Number of updated conversations
            notes: Optional notes
            
        Returns:
            run_id for this training run
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO training_runs 
                (run_type, started_at, num_conversations, num_new, num_updated, 
                 status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_type,
                    datetime.now().timestamp(),
                    num_conversations,
                    num_new,
                    num_updated,
                    'running',
                    notes
                )
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()
    
    def complete_training_run(
        self,
        run_id: int,
        status: str = 'completed',
        metrics: Optional[str] = None
    ):
        """
        Mark a training run as complete.
        
        Args:
            run_id: Training run ID
            status: Status ('completed', 'failed', 'cancelled')
            metrics: Optional JSON string with metrics
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE training_runs
                SET completed_at = ?, status = ?, metrics = ?
                WHERE run_id = ?
                """,
                (datetime.now().timestamp(), status, metrics, run_id)
            )
            conn.commit()
        finally:
            conn.close()
    
    def get_training_runs(self, limit: int = 10) -> List[Dict]:
        """
        Get recent training runs.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of training run dicts
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT run_id, run_type, started_at, completed_at, 
                       num_conversations, num_new, num_updated, status, 
                       metrics, notes
                FROM training_runs
                ORDER BY run_id DESC
                LIMIT ?
                """,
                (limit,)
            )
            
            runs = []
            for row in cur.fetchall():
                runs.append({
                    'run_id': row[0],
                    'run_type': row[1],
                    'started_at': row[2],
                    'completed_at': row[3],
                    'num_conversations': row[4],
                    'num_new': row[5],
                    'num_updated': row[6],
                    'status': row[7],
                    'metrics': row[8],
                    'notes': row[9]
                })
            
            return runs
        finally:
            conn.close()
    
    def save_checkpoint(
        self,
        model_path: str,
        vector_store_path: str,
        num_vectors: int,
        model_version: str = '0.1.0',
        description: Optional[str] = None
    ) -> int:
        """
        Save a model checkpoint record.
        
        Args:
            model_path: Path to saved model
            vector_store_path: Path to saved vector store
            num_vectors: Number of vectors in store
            model_version: Model version
            description: Optional description
            
        Returns:
            checkpoint_id
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO model_checkpoints
                (created_at, model_path, vector_store_path, num_vectors, 
                 model_version, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().timestamp(),
                    model_path,
                    vector_store_path,
                    num_vectors,
                    model_version,
                    description
                )
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()
    
    def get_latest_checkpoint(self) -> Optional[Dict]:
        """
        Get the most recent checkpoint.
        
        Returns:
            Checkpoint dict or None
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT checkpoint_id, created_at, model_path, vector_store_path,
                       num_vectors, model_version, description
                FROM model_checkpoints
                ORDER BY checkpoint_id DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                'checkpoint_id': row[0],
                'created_at': row[1],
                'model_path': row[2],
                'vector_store_path': row[3],
                'num_vectors': row[4],
                'model_version': row[5],
                'description': row[6]
            }
        finally:
            conn.close()
    
    def get_stats(self) -> Dict:
        """
        Get overall training statistics.
        
        Returns:
            Dict with statistics
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            
            # Count trained conversations
            cur.execute("SELECT COUNT(*) FROM trained_conversations")
            num_trained = cur.fetchone()[0]
            
            # Count training runs
            cur.execute("SELECT COUNT(*) FROM training_runs")
            num_runs = cur.fetchone()[0]
            
            # Count checkpoints
            cur.execute("SELECT COUNT(*) FROM model_checkpoints")
            num_checkpoints = cur.fetchone()[0]
            
            # Get latest run info
            cur.execute(
                """
                SELECT run_type, started_at, status
                FROM training_runs
                ORDER BY run_id DESC
                LIMIT 1
                """
            )
            latest_run = cur.fetchone()
            latest_run_info = None
            if latest_run:
                latest_run_info = {
                    'run_type': latest_run[0],
                    'started_at': datetime.fromtimestamp(latest_run[1]).strftime(
                        '%Y-%m-%d %H:%M:%S'
                    ),
                    'status': latest_run[2]
                }
            
            return {
                'num_trained_conversations': num_trained,
                'num_training_runs': num_runs,
                'num_checkpoints': num_checkpoints,
                'latest_run': latest_run_info
            }
        finally:
            conn.close()
