"""
Context Manager

Tracks conversation context for follow-up questions.
Enables users to say "how about this month?" after asking about last month.
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class QueryContext:
    """
    Stores context for a single query.
    """
    
    def __init__(
        self,
        question: str,
        sql: str,
        results: list,
        timestamp: datetime
    ):
        self.question = question
        self.sql = sql
        self.results = results
        self.timestamp = timestamp
        self.row_count = len(results) if results else 0


class ContextManager:
    """
    Manages query context per user for follow-up questions.
    
    Enables:
    - "What was revenue last month?" → saves context
    - "How about this month?" → uses previous context
    - "Show it by region" → modifies previous query
    """
    
    def __init__(self, max_age_minutes: int = 30):
        """
        Initialize context manager.
        
        Args:
            max_age_minutes: How long to keep context (default 30 min)
        """
        self.contexts: Dict[str, QueryContext] = {}
        self.max_age = timedelta(minutes=max_age_minutes)
        
        logger.info(f"✅ Context manager initialized (max_age={max_age_minutes}m)")
    
    def save_context(
        self,
        user_id: str,
        question: str,
        sql: str,
        results: list
    ):
        """
        Save query context for a user.
        
        Args:
            user_id: Slack user ID
            question: User's question
            sql: Generated SQL
            results: Query results
        """
        context = QueryContext(
            question=question,
            sql=sql,
            results=results,
            timestamp=datetime.now()
        )
        
        self.contexts[user_id] = context
        
        logger.info(
            f"💾 Saved context for {user_id}: "
            f"question=\"{question[:50]}\", "
            f"rows={len(results)}"
        )
    
    def get_context(self, user_id: str) -> Optional[QueryContext]:
        """
        Get user's previous query context if recent enough.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            QueryContext if exists and not expired, else None
        """
        if user_id not in self.contexts:
            return None
        
        context = self.contexts[user_id]
        age = datetime.now() - context.timestamp
        
        if age > self.max_age:
            # Context expired
            logger.info(f"⏰ Context expired for {user_id} (age={age})")
            del self.contexts[user_id]
            return None
        
        logger.info(
            f"✅ Retrieved context for {user_id}: "
            f"question=\"{context.question[:50]}\""
        )
        return context
    
    def clear_context(self, user_id: str):
        """
        Clear context for a user.
        
        Args:
            user_id: Slack user ID
        """
        if user_id in self.contexts:
            del self.contexts[user_id]
            logger.info(f"🗑️ Cleared context for {user_id}")
    
    def is_follow_up(self, question: str) -> bool:
        """
        Detect if question is likely a follow-up.
        
        Patterns:
        - "how about X"
        - "what about X"
        - "show it by X"
        - "for this X"
        - Just "this month" (without "what was revenue")
        
        Args:
            question: User's question
        
        Returns:
            True if likely a follow-up question
        """
        question_lower = question.lower().strip()
        
        # Follow-up patterns
        patterns = [
            'how about',
            'what about',
            'show it',
            'for this',
            'for last',
            'instead',
            'rather than',
            'grouped by',
            'by region',
            'by department',
            'by product',
        ]
        
        # Short questions without verbs are usually follow-ups
        if len(question_lower.split()) <= 3:
            return True
        
        return any(pattern in question_lower for pattern in patterns)
    
    def build_context_prompt(
        self,
        question: str,
        previous_context: QueryContext
    ) -> str:
        """
        Build enriched prompt with previous context.
        
        Args:
            question: Current question
            previous_context: Previous query context
        
        Returns:
            Enhanced question with context
        """
        return (
            f"Previous question: {previous_context.question}\n"
            f"Previous SQL: {previous_context.sql}\n\n"
            f"Follow-up question: {question}\n\n"
            f"Generate SQL for the follow-up question, "
            f"using context from the previous question."
        )
    
    def cleanup_expired(self):
        """Remove all expired contexts."""
        now = datetime.now()
        expired = [
            user_id
            for user_id, ctx in self.contexts.items()
            if now - ctx.timestamp > self.max_age
        ]
        
        for user_id in expired:
            del self.contexts[user_id]
        
        if expired:
            logger.info(f"🗑️ Cleaned up {len(expired)} expired contexts")
    
    def get_stats(self) -> Dict:
        """
        Get context statistics.
        
        Returns:
            Dict with stats
        """
        return {
            "total_contexts": len(self.contexts),
            "users_with_context": list(self.contexts.keys())
        }