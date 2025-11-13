"""
Data Loader Module

Loads and parses pruned.json data with support for incremental detection
of new or updated conversations based on metadata.db tracking.
"""

import json
import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple


logger = logging.getLogger(__name__)


class ConversationData:
    """Represents a single conversation with metadata."""
    
    def __init__(
        self,
        conv_id: str,
        title: str,
        create_time: str,
        update_time: str,
        messages: List[Dict[str, str]]
    ):
        self.id = conv_id
        self.title = title
        self.create_time = create_time
        self.update_time = update_time
        self.messages = messages
        
    def get_full_text(self) -> str:
        """Get concatenated text of all messages."""
        return "\n".join([f"{msg['author']}: {msg['text']}" for msg in self.messages])
    
    def get_user_messages(self) -> List[str]:
        """Get only user messages."""
        return [msg['text'] for msg in self.messages if msg['author'] in ('user', 'User')]
    
    def get_assistant_messages(self) -> List[str]:
        """Get only assistant messages."""
        return [msg['text'] for msg in self.messages if msg['author'] == 'ChatGPT']
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'id': self.id,
            'title': self.title,
            'create_time': self.create_time,
            'update_time': self.update_time,
            'messages': self.messages
        }


class DataLoader:
    """Loads conversation data from pruned.json with incremental tracking."""
    
    def __init__(self, data_dir: str):
        """
        Initialize data loader.
        
        Args:
            data_dir: Directory containing pruned.json and metadata.db
        """
        self.data_dir = data_dir
        self.pruned_json_path = os.path.join(data_dir, 'pruned.json')
        self.metadata_db_path = os.path.join(data_dir, 'metadata.db')
        
    def load_all_conversations(self) -> List[ConversationData]:
        """
        Load all conversations from pruned.json.
        
        Returns:
            List of ConversationData objects
        """
        if not os.path.exists(self.pruned_json_path):
            raise FileNotFoundError(f"pruned.json not found at {self.pruned_json_path}")
        
        with open(self.pruned_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conversations = []
        for month, entries in data.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                conv = ConversationData(
                    conv_id=entry.get('id', ''),
                    title=entry.get('title', ''),
                    create_time=entry.get('create_time', ''),
                    update_time=entry.get('update_time', ''),
                    messages=entry.get('messages', [])
                )
                conversations.append(conv)
        
        logger.info(f"Loaded {len(conversations)} conversations from pruned.json")
        return conversations
    
    def get_new_or_updated_conversations(
        self,
        training_db_path: str
    ) -> Tuple[List[ConversationData], List[ConversationData]]:
        """
        Identify new or updated conversations since last training run.
        
        Args:
            training_db_path: Path to training tracker database
            
        Returns:
            Tuple of (new_conversations, updated_conversations)
        """
        all_convs = self.load_all_conversations()
        
        # If training DB doesn't exist, all conversations are new
        if not os.path.exists(training_db_path):
            logger.info("No training database found - treating all conversations as new")
            return all_convs, []
        
        # Load processed conversation IDs and update times from training DB
        conn = sqlite3.connect(training_db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT conv_id, update_time FROM trained_conversations"
            )
            trained = {row[0]: row[1] for row in cur.fetchall()}
        finally:
            conn.close()
        
        new_convs = []
        updated_convs = []
        
        for conv in all_convs:
            if conv.id not in trained:
                new_convs.append(conv)
            else:
                # Check if update_time changed
                try:
                    conv_update_dt = datetime.strptime(
                        conv.update_time, '%Y-%m-%d %H:%M:%S'
                    )
                    conv_update_ts = conv_update_dt.timestamp()
                    
                    if conv_update_ts > float(trained[conv.id]):
                        updated_convs.append(conv)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse update time for {conv.id}: {e}")
                    continue
        
        logger.info(
            f"Found {len(new_convs)} new and {len(updated_convs)} updated conversations"
        )
        return new_convs, updated_convs
    
    def get_conversations_since(self, since_date: str) -> List[ConversationData]:
        """
        Get conversations updated on or after a specific date.
        
        Args:
            since_date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            List of ConversationData objects
        """
        since_dt = datetime.strptime(since_date, '%Y-%m-%d')
        since_ts = since_dt.timestamp()
        
        all_convs = self.load_all_conversations()
        filtered = []
        
        for conv in all_convs:
            try:
                conv_update_dt = datetime.strptime(
                    conv.update_time, '%Y-%m-%d %H:%M:%S'
                )
                if conv_update_dt.timestamp() >= since_ts:
                    filtered.append(conv)
            except (ValueError, TypeError):
                continue
        
        logger.info(
            f"Found {len(filtered)} conversations updated since {since_date}"
        )
        return filtered
    
    def get_conversation_by_id(self, conv_id: str) -> Optional[ConversationData]:
        """
        Get a specific conversation by ID.
        
        Args:
            conv_id: Conversation ID
            
        Returns:
            ConversationData or None if not found
        """
        all_convs = self.load_all_conversations()
        for conv in all_convs:
            if conv.id == conv_id:
                return conv
        return None
    
    def get_stats(self) -> Dict:
        """
        Get statistics about loaded conversations.
        
        Returns:
            Dictionary with stats (total count, date range, etc.)
        """
        convs = self.load_all_conversations()
        
        if not convs:
            return {
                'total_conversations': 0,
                'total_messages': 0,
                'date_range': None
            }
        
        total_messages = sum(len(conv.messages) for conv in convs)
        
        # Parse dates to find range
        dates = []
        for conv in convs:
            try:
                dt = datetime.strptime(conv.update_time, '%Y-%m-%d %H:%M:%S')
                dates.append(dt)
            except (ValueError, TypeError):
                continue
        
        date_range = None
        if dates:
            date_range = {
                'earliest': min(dates).strftime('%Y-%m-%d'),
                'latest': max(dates).strftime('%Y-%m-%d')
            }
        
        return {
            'total_conversations': len(convs),
            'total_messages': total_messages,
            'date_range': date_range,
            'avg_messages_per_conversation': (
                total_messages / len(convs) if convs else 0
            )
        }
