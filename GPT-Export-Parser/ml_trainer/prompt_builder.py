"""
Prompt Builder Module

Context-aware prompt construction assistant that uses retrieved conversation
history to suggest relevant context and phrasing.
"""

import logging
from typing import List, Dict, Optional, Tuple
from collections import Counter

from .retrieval import ConversationRetriever

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Assists with building context-aware prompts using conversation history."""
    
    def __init__(self, retriever: ConversationRetriever):
        """
        Initialize prompt builder.
        
        Args:
            retriever: ConversationRetriever instance
        """
        self.retriever = retriever
    
    def suggest_context(
        self,
        current_prompt: str,
        k: int = 3,
        include_snippets: bool = True
    ) -> Dict:
        """
        Suggest relevant historical context for a prompt.
        
        Args:
            current_prompt: The prompt being constructed
            k: Number of relevant conversations to retrieve
            include_snippets: Whether to include text snippets
            
        Returns:
            Dict with suggestions and context
        """
        # Retrieve relevant conversations
        results = self.retriever.retrieve(current_prompt, k=k, return_scores=True)
        
        suggestions = {
            'query': current_prompt,
            'num_results': len(results),
            'relevant_conversations': [],
            'suggested_topics': [],
            'common_patterns': []
        }
        
        # Extract topics and patterns
        all_titles = []
        all_texts = []
        
        for result in results:
            conv_info = {
                'title': result.get('title', 'Untitled'),
                'date': result.get('update_time', 'Unknown'),
                'similarity_score': result.get('similarity_score', 0.0)
            }
            
            if include_snippets:
                text = result.get('text', '')
                # Include first 200 chars as snippet
                conv_info['snippet'] = text[:200] + ('...' if len(text) > 200 else '')
            
            suggestions['relevant_conversations'].append(conv_info)
            all_titles.append(result.get('title', ''))
            all_texts.append(result.get('text', ''))
        
        # Extract common topics from titles
        title_words = []
        for title in all_titles:
            words = [w.lower() for w in title.split() if len(w) > 3]
            title_words.extend(words)
        
        if title_words:
            common_topics = Counter(title_words).most_common(5)
            suggestions['suggested_topics'] = [word for word, _ in common_topics]
        
        # Identify common patterns in conversations
        patterns = self._identify_patterns(all_texts)
        suggestions['common_patterns'] = patterns
        
        logger.info(f"Generated context suggestions for prompt: {current_prompt[:50]}...")
        return suggestions
    
    def _identify_patterns(self, texts: List[str]) -> List[str]:
        """
        Identify common patterns in conversation texts.
        
        Args:
            texts: List of conversation texts
            
        Returns:
            List of identified patterns
        """
        patterns = []
        
        # Check for questions
        question_count = sum(1 for text in texts if '?' in text)
        if question_count >= len(texts) * 0.5:
            patterns.append("Contains questions")
        
        # Check for code
        code_indicators = ['```', 'def ', 'function ', 'class ', 'import ', 'const ']
        code_count = sum(
            1 for text in texts
            if any(indicator in text for indicator in code_indicators)
        )
        if code_count >= len(texts) * 0.3:
            patterns.append("Contains code")
        
        # Check for explanations
        explanation_words = ['because', 'therefore', 'however', 'explanation', 'reason']
        explanation_count = sum(
            1 for text in texts
            if any(word in text.lower() for word in explanation_words)
        )
        if explanation_count >= len(texts) * 0.5:
            patterns.append("Contains explanations")
        
        return patterns
    
    def build_enhanced_prompt(
        self,
        current_prompt: str,
        k: int = 2,
        include_context: bool = True,
        format_style: str = 'concise'
    ) -> str:
        """
        Build an enhanced prompt with relevant historical context.
        
        Args:
            current_prompt: The base prompt
            k: Number of relevant conversations to include
            include_context: Whether to prepend context
            format_style: Style of context formatting ('concise', 'detailed')
            
        Returns:
            Enhanced prompt string
        """
        if not include_context:
            return current_prompt
        
        # Get relevant context
        results, context_text = self.retriever.get_context_window(
            current_prompt,
            k=k,
            max_tokens=1000 if format_style == 'concise' else 2000
        )
        
        if not results:
            return current_prompt
        
        # Format enhanced prompt
        if format_style == 'concise':
            context_summary = f"Relevant past discussions ({len(results)} found):\n"
            for i, result in enumerate(results, 1):
                title = result.get('title', 'Untitled')
                context_summary += f"{i}. {title}\n"
            
            enhanced = f"{context_summary}\nCurrent question: {current_prompt}"
        else:
            # Detailed format
            enhanced = f"Context from past conversations:\n\n{context_text}\n"
            enhanced += f"Current question: {current_prompt}"
        
        logger.info(f"Built enhanced prompt with {len(results)} context items")
        return enhanced
    
    def suggest_follow_up_questions(
        self,
        topic: str,
        k: int = 5
    ) -> List[str]:
        """
        Suggest follow-up questions based on historical conversations.
        
        Args:
            topic: Topic to generate questions for
            k: Number of conversations to analyze
            
        Returns:
            List of suggested questions
        """
        # Retrieve conversations about topic
        results = self.retriever.retrieve_by_topic(topic, k=k)
        
        if not results:
            return []
        
        suggestions = []
        
        # Extract questions from conversation texts
        for result in results:
            text = result.get('text', '')
            # Simple question extraction (look for '?')
            sentences = text.split('\n')
            questions = [s.strip() for s in sentences if '?' in s]
            
            # Take first question from each conversation
            if questions:
                suggestions.append(questions[0])
        
        # Limit to unique suggestions
        unique_suggestions = list(dict.fromkeys(suggestions))[:5]
        
        logger.info(f"Generated {len(unique_suggestions)} follow-up question suggestions")
        return unique_suggestions
    
    def get_prompt_history_stats(self, prompt: str) -> Dict:
        """
        Get statistics about how similar prompts were used historically.
        
        Args:
            prompt: Prompt to analyze
            
        Returns:
            Dict with historical usage statistics
        """
        # Retrieve similar conversations
        results = self.retriever.retrieve(prompt, k=10, return_scores=True)
        
        if not results:
            return {
                'similar_conversations_count': 0,
                'date_range': None,
                'avg_similarity': 0.0
            }
        
        # Compute statistics
        similarities = [r.get('similarity_score', 0.0) for r in results]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        
        dates = [r.get('update_time', '') for r in results if r.get('update_time')]
        date_range = None
        if dates:
            sorted_dates = sorted(dates)
            date_range = {
                'earliest': sorted_dates[0],
                'latest': sorted_dates[-1]
            }
        
        return {
            'similar_conversations_count': len(results),
            'date_range': date_range,
            'avg_similarity': avg_similarity,
            'most_similar': results[0] if results else None
        }
    
    def extract_key_phrases(
        self,
        prompt: str,
        k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Extract key phrases from conversations related to prompt.
        
        Args:
            prompt: Prompt to analyze
            k: Number of conversations to analyze
            
        Returns:
            List of (phrase, frequency) tuples
        """
        results = self.retriever.retrieve(prompt, k=k)
        
        if not results:
            return []
        
        # Combine all texts
        all_text = ' '.join([r.get('text', '') for r in results])
        
        # Simple phrase extraction (2-3 word combinations)
        words = all_text.lower().split()
        phrases = []
        
        # Extract 2-word phrases
        for i in range(len(words) - 1):
            if len(words[i]) > 3 and len(words[i+1]) > 3:
                phrase = f"{words[i]} {words[i+1]}"
                phrases.append(phrase)
        
        # Count frequencies
        phrase_counts = Counter(phrases)
        top_phrases = phrase_counts.most_common(10)
        
        # Normalize frequencies
        max_count = top_phrases[0][1] if top_phrases else 1
        normalized = [(phrase, count / max_count) for phrase, count in top_phrases]
        
        logger.info(f"Extracted {len(normalized)} key phrases")
        return normalized
