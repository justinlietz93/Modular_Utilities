"""
Thread Detector Module

Identifies open/unresolved threads and important follow-ups from conversation history.
"""

import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta

from .data_loader import ConversationData

logger = logging.getLogger(__name__)

# Constants for thread detection scoring
OPEN_THREAD_THRESHOLD = 0.3  # Threshold for identifying likely open threads
OPEN_INDICATOR_WEIGHT = 0.15  # Weight per open indicator found
MAX_OPEN_INDICATOR_SCORE = 0.5  # Maximum score from open indicators
QUESTION_WEIGHT = 0.3  # Weight for unresolved questions
RESOLUTION_PENALTY = 0.1  # Penalty per resolution indicator found
MAX_RESOLUTION_PENALTY = 0.3  # Maximum penalty from resolution indicators


class ThreadDetector:
    """Detects open threads and unresolved questions in conversations."""
    
    def __init__(self):
        """Initialize thread detector."""
        # Keywords that indicate open threads
        self.open_indicators = [
            'todo', 'to do', 'will do', 'need to', 'should', 'must',
            'follow up', 'later', 'next time', 'remind', 'remember',
            'continue', 'unfinished', 'incomplete', 'pending'
        ]
        
        # Keywords that indicate questions
        self.question_indicators = [
            '?', 'how', 'what', 'when', 'where', 'why', 'which',
            'can you', 'could you', 'would you', 'do you'
        ]
        
        # Keywords that indicate resolution
        self.resolution_indicators = [
            'solved', 'fixed', 'done', 'completed', 'resolved',
            'finished', 'works', 'working', 'success', 'thank'
        ]
    
    def detect_open_threads(
        self,
        conversations: List[ConversationData],
        days_threshold: int = 30,
        min_messages: int = 3
    ) -> List[Dict]:
        """
        Detect conversations with likely open threads.
        
        Args:
            conversations: List of ConversationData objects
            days_threshold: Consider conversations from last N days
            min_messages: Minimum messages to consider
            
        Returns:
            List of dicts with open thread information
        """
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        open_threads = []
        
        for conv in conversations:
            # Filter by date
            try:
                update_dt = datetime.strptime(conv.update_time, '%Y-%m-%d %H:%M:%S')
                if update_dt < cutoff_date:
                    continue
            except (ValueError, TypeError):
                continue
            
            # Filter by message count
            if len(conv.messages) < min_messages:
                continue
            
            # Analyze conversation for open indicators
            score = self._calculate_open_thread_score(conv)
            
            if score > OPEN_THREAD_THRESHOLD:  # Threshold for "likely open"
                thread_info = {
                    'conv_id': conv.id,
                    'title': conv.title,
                    'update_time': conv.update_time,
                    'score': score,
                    'indicators': self._extract_indicators(conv),
                    'last_message': conv.messages[-1] if conv.messages else None
                }
                open_threads.append(thread_info)
        
        # Sort by score (most likely open first)
        open_threads.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"Detected {len(open_threads)} potential open threads")
        return open_threads
    
    def _calculate_open_thread_score(self, conv: ConversationData) -> float:
        """
        Calculate a score indicating likelihood of open thread.
        
        Args:
            conv: ConversationData object
            
        Returns:
            Score between 0 and 1
        """
        score = 0.0
        full_text = conv.get_full_text().lower()
        
        # Check for open indicators
        open_count = sum(
            1 for indicator in self.open_indicators
            if indicator in full_text
        )
        score += min(open_count * OPEN_INDICATOR_WEIGHT, MAX_OPEN_INDICATOR_SCORE)
        
        # Check for unresolved questions (questions without answers)
        last_messages = conv.messages[-3:] if len(conv.messages) >= 3 else conv.messages
        last_is_question = any(
            indicator in last_messages[-1]['text'].lower()
            for indicator in self.question_indicators
        )
        if last_is_question:
            score += QUESTION_WEIGHT
        
        # Penalize if resolution indicators present
        resolution_count = sum(
            1 for indicator in self.resolution_indicators
            if indicator in full_text
        )
        score -= min(resolution_count * RESOLUTION_PENALTY, MAX_RESOLUTION_PENALTY)
        
        # Normalize to [0, 1]
        return max(0.0, min(1.0, score))
    
    def _extract_indicators(self, conv: ConversationData) -> List[str]:
        """
        Extract specific indicators from conversation.
        
        Args:
            conv: ConversationData object
            
        Returns:
            List of indicator phrases found
        """
        full_text = conv.get_full_text().lower()
        found_indicators = []
        
        for indicator in self.open_indicators:
            if indicator in full_text:
                found_indicators.append(indicator)
        
        return found_indicators[:5]  # Limit to first 5
    
    def detect_unanswered_questions(
        self,
        conversations: List[ConversationData],
        days_threshold: int = 14
    ) -> List[Dict]:
        """
        Detect conversations ending with unanswered questions.
        
        Args:
            conversations: List of ConversationData objects
            days_threshold: Consider conversations from last N days
            
        Returns:
            List of dicts with unanswered question info
        """
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        unanswered = []
        
        for conv in conversations:
            # Filter by date
            try:
                update_dt = datetime.strptime(conv.update_time, '%Y-%m-%d %H:%M:%S')
                if update_dt < cutoff_date:
                    continue
            except (ValueError, TypeError):
                continue
            
            if not conv.messages:
                continue
            
            # Check if last message is from user and contains question
            last_msg = conv.messages[-1]
            if last_msg['author'] in ('user', 'User'):
                if any(
                    indicator in last_msg['text'].lower()
                    for indicator in self.question_indicators
                ):
                    unanswered.append({
                        'conv_id': conv.id,
                        'title': conv.title,
                        'update_time': conv.update_time,
                        'question': last_msg['text'][:200]  # First 200 chars
                    })
        
        logger.info(f"Detected {len(unanswered)} unanswered questions")
        return unanswered
    
    def detect_action_items(
        self,
        conversations: List[ConversationData],
        days_threshold: int = 30
    ) -> List[Dict]:
        """
        Detect action items mentioned in conversations.
        
        Args:
            conversations: List of ConversationData objects
            days_threshold: Consider conversations from last N days
            
        Returns:
            List of dicts with action item info
        """
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        action_items = []
        
        action_keywords = [
            'need to', 'should', 'must', 'have to', 'will',
            'todo', 'task', 'action', 'implement', 'fix',
            'create', 'build', 'develop', 'test'
        ]
        
        for conv in conversations:
            # Filter by date
            try:
                update_dt = datetime.strptime(conv.update_time, '%Y-%m-%d %H:%M:%S')
                if update_dt < cutoff_date:
                    continue
            except (ValueError, TypeError):
                continue
            
            # Look for action items in messages
            for msg in conv.messages:
                text_lower = msg['text'].lower()
                
                for keyword in action_keywords:
                    if keyword in text_lower:
                        # Extract sentence containing keyword
                        sentences = msg['text'].split('.')
                        relevant_sentences = [
                            s.strip() for s in sentences
                            if keyword in s.lower()
                        ]
                        
                        if relevant_sentences:
                            action_items.append({
                                'conv_id': conv.id,
                                'title': conv.title,
                                'update_time': conv.update_time,
                                'action': relevant_sentences[0][:200],
                                'keyword': keyword
                            })
                            break  # Only one action per message
        
        logger.info(f"Detected {len(action_items)} action items")
        return action_items
    
    def get_thread_summary(
        self,
        conversations: List[ConversationData],
        days_threshold: int = 30
    ) -> Dict:
        """
        Get comprehensive summary of thread status.
        
        Args:
            conversations: List of ConversationData objects
            days_threshold: Consider conversations from last N days
            
        Returns:
            Dict with summary statistics
        """
        open_threads = self.detect_open_threads(
            conversations,
            days_threshold=days_threshold
        )
        unanswered = self.detect_unanswered_questions(
            conversations,
            days_threshold=days_threshold
        )
        actions = self.detect_action_items(
            conversations,
            days_threshold=days_threshold
        )
        
        # Count conversations in time window
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        recent_count = 0
        for conv in conversations:
            try:
                update_dt = datetime.strptime(conv.update_time, '%Y-%m-%d %H:%M:%S')
                if update_dt >= cutoff_date:
                    recent_count += 1
            except (ValueError, TypeError):
                continue
        
        summary = {
            'days_analyzed': days_threshold,
            'total_recent_conversations': recent_count,
            'open_threads_count': len(open_threads),
            'unanswered_questions_count': len(unanswered),
            'action_items_count': len(actions),
            'top_open_threads': open_threads[:5],
            'recent_unanswered': unanswered[:5],
            'priority_actions': actions[:5]
        }
        
        logger.info(
            f"Thread summary: {summary['open_threads_count']} open, "
            f"{summary['unanswered_questions_count']} unanswered, "
            f"{summary['action_items_count']} actions"
        )
        
        return summary
