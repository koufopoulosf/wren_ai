"""
Context Manager

Manages conversation context and memory for strong conversational AI.

This module provides comprehensive context management including:
- Full conversation history (not truncated)
- Entity tracking across messages
- Reference resolution ("show me more", "what about X?")
- Semantic search of past interactions
- Context summarization for long conversations
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import json
from anthropic import Anthropic

from llm_utils import LLMUtils
from constants import (
    LLM_MAX_TOKENS_CLASSIFICATION,
    LLM_TEMPERATURE_PRECISE
)
from exceptions import LLMError

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """
    Single conversation turn.

    Stores complete message with metadata - nothing truncated!
    """
    timestamp: datetime
    role: str  # 'user' or 'assistant'
    content: str  # Full text (NOT truncated)
    sql: Optional[str] = None  # Generated SQL if applicable
    results: Optional[List[Dict]] = None  # Query results if applicable
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'role': self.role,
            'content': self.content,
            'sql': self.sql,
            'results': self.results,
            'metadata': self.metadata
        }


@dataclass
class ConversationContext:
    """
    Rich conversation context with full history.

    Maintains complete conversation state including:
    - All messages (full text, not truncated)
    - Mentioned entities (tokens, time periods, metrics)
    - Conversation state (what we're discussing)
    - Previous queries for reference
    """
    session_id: str
    messages: List[Message] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)  # Track mentioned entities
    state: Dict[str, Any] = field(default_factory=dict)  # Conversation state
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def add_message(self, message: Message):
        """Add message to history."""
        self.messages.append(message)
        self.last_updated = datetime.now()

    def get_recent_messages(self, n: int = 5) -> List[Message]:
        """Get last N messages."""
        return self.messages[-n:]

    def get_last_sql_query(self) -> Optional[str]:
        """Get the most recent SQL query."""
        for msg in reversed(self.messages):
            if msg.sql:
                return msg.sql
        return None

    def get_last_results(self) -> Optional[List[Dict]]:
        """Get the most recent query results."""
        for msg in reversed(self.messages):
            if msg.results:
                return msg.results
        return None


class ContextManager:
    """
    Manages conversation context and memory.

    Provides:
    - Full conversation history storage
    - Entity tracking (mentioned tokens, dates, etc.)
    - Reference resolution ("show me more" → understands context)
    - Semantic search of past queries
    - Context summarization for long conversations
    """

    def __init__(self, anthropic_client: Anthropic, model: str):
        """
        Initialize context manager.

        Args:
            anthropic_client: Anthropic API client for LLM calls
            model: Claude model name
        """
        self.client = anthropic_client
        self.model = model
        self.contexts: Dict[str, ConversationContext] = {}  # session_id -> context
        logger.info("✅ Context manager initialized")

    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """
        Get context for session, creating if needed.

        Args:
            session_id: Unique session identifier

        Returns:
            ConversationContext for this session
        """
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(session_id=session_id)
            logger.info(f"Created new context for session: {session_id}")

        return self.contexts[session_id]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sql: Optional[str] = None,
        results: Optional[List[Dict]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add message to conversation history.

        Args:
            session_id: Session identifier
            role: 'user' or 'assistant'
            content: Message content (full text, not truncated!)
            sql: Generated SQL if applicable
            results: Query results if applicable
            metadata: Additional context
        """
        context = self.get_or_create_context(session_id)

        message = Message(
            timestamp=datetime.now(),
            role=role,
            content=content,
            sql=sql,
            results=results,
            metadata=metadata or {}
        )

        context.add_message(message)
        logger.debug(f"Added {role} message to session {session_id} (total: {len(context.messages)})")

    async def resolve_references(
        self,
        question: str,
        session_id: str
    ) -> str:
        """
        Resolve references and pronouns in question.

        Examples:
        - "Show me more" → "Show me more Bitcoin price data"
        - "What about Ethereum?" → "What was Ethereum price last week?"
        - "How about last month?" → "What was Bitcoin price last month?"

        Args:
            question: User's potentially ambiguous question
            session_id: Session identifier for context

        Returns:
            Resolved question with full context
        """
        logger.debug(f"Resolving references for question: {question[:100]}...")
        context = self.get_or_create_context(session_id)

        # If no history, return as-is
        if not context.messages:
            logger.debug("No conversation history - returning question as-is")
            return question

        # Check if question needs resolution
        if not self._needs_resolution(question):
            logger.debug("Question does not need resolution - returning as-is")
            return question

        logger.info(f"Question needs resolution (session: {session_id}, history: {len(context.messages)} messages)")

        try:
            # Build context from recent messages
            recent_history = self._build_history_summary(context)
            last_query = context.get_last_sql_query()

            # Create resolution prompt
            prompt = f"""You are helping resolve ambiguous references in a user's question.

Recent conversation:
{recent_history}

Last SQL query: {last_query if last_query else "None"}

User's new question: "{question}"

The question contains references like "more", "that", "it", "this", etc.
Resolve these references based on the conversation context.

Respond with ONLY the resolved question, nothing else.

Examples:
- "Show me more" → "Show me more Bitcoin price data"
- "What about Ethereum?" → "What about Ethereum price?"
- "How about last month?" → "What was Bitcoin price last month?"

Resolved question:"""

            resolved = await LLMUtils.call_claude_async(
                client=self.client,
                model=self.model,
                prompt=prompt,
                max_tokens=LLM_MAX_TOKENS_CLASSIFICATION,
                temperature=LLM_TEMPERATURE_PRECISE
            )

            logger.info(f"Resolved reference: '{question}' → '{resolved}'")
            return resolved.strip()

        except LLMError as e:
            logger.warning(f"Reference resolution failed: {e}, using original question")
            return question

    def _needs_resolution(self, question: str) -> bool:
        """
        Check if question needs reference resolution.

        Args:
            question: User's question

        Returns:
            True if question likely contains references
        """
        question_lower = question.lower()

        # Indicators that question needs resolution
        reference_words = [
            'more', 'that', 'this', 'it', 'same', 'those', 'these',
            'what about', 'how about', 'show me', 'tell me about'
        ]

        return any(word in question_lower for word in reference_words)

    def _build_history_summary(self, context: ConversationContext, max_messages: int = 5) -> str:
        """
        Build summary of recent conversation history.

        Args:
            context: Conversation context
            max_messages: Maximum messages to include

        Returns:
            Formatted history summary
        """
        recent = context.get_recent_messages(max_messages)

        if not recent:
            return "No previous conversation."

        lines = []
        for msg in recent:
            role = msg.role.capitalize()
            content = msg.content

            # Include SQL if present
            if msg.sql:
                lines.append(f"{role}: {content}")
                lines.append(f"  SQL: {msg.sql}")
            else:
                lines.append(f"{role}: {content}")

        return "\n".join(lines)

    async def extract_entities(
        self,
        question: str,
        session_id: str
    ) -> Dict[str, List[str]]:
        """
        Extract entities from question and track them.

        Entities include:
        - Cryptocurrencies (Bitcoin, Ethereum, etc.)
        - Time periods (last month, Q3 2024, etc.)
        - Metrics (price, volume, holdings, etc.)
        - Users/accounts

        Args:
            question: User's question
            session_id: Session identifier

        Returns:
            Dictionary of entity types to entity values
        """
        context = self.get_or_create_context(session_id)

        try:
            prompt = f"""Extract entities from this question about cryptocurrency trading data.

Question: "{question}"

Identify:
- Cryptocurrencies/tokens (BTC, Bitcoin, Ethereum, etc.)
- Time periods (last month, Q3 2024, yesterday, etc.)
- Metrics (price, volume, trading volume, holdings, etc.)
- Other relevant entities

Respond with JSON only:
{{
  "cryptocurrencies": ["Bitcoin", "Ethereum"],
  "time_periods": ["last month"],
  "metrics": ["price", "volume"]
}}"""

            response = await LLMUtils.call_claude_async(
                client=self.client,
                model=self.model,
                prompt=prompt,
                max_tokens=LLM_MAX_TOKENS_CLASSIFICATION,
                temperature=LLM_TEMPERATURE_PRECISE
            )

            entities = json.loads(response)

            # Update context entities
            for entity_type, values in entities.items():
                if entity_type not in context.entities:
                    context.entities[entity_type] = []

                # Add new entities, avoiding duplicates
                for value in values:
                    if value not in context.entities[entity_type]:
                        context.entities[entity_type].append(value)

            logger.debug(f"Extracted entities: {entities}")
            return entities

        except (LLMError, json.JSONDecodeError) as e:
            logger.warning(f"Entity extraction failed: {e}")
            return {}

    def get_conversation_summary(self, session_id: str, max_length: int = 500) -> str:
        """
        Get concise summary of conversation so far.

        Useful for long conversations to provide context without
        overwhelming the prompt.

        Args:
            session_id: Session identifier
            max_length: Maximum characters in summary

        Returns:
            Concise conversation summary
        """
        context = self.get_or_create_context(session_id)

        if not context.messages:
            return "New conversation."

        # Build simple summary from recent messages
        recent = context.get_recent_messages(10)

        summary_parts = []
        for msg in recent:
            if msg.role == 'user':
                summary_parts.append(f"User asked: {msg.content[:100]}")
            else:
                summary_parts.append(f"Assistant: {msg.content[:100]}")

        summary = " | ".join(summary_parts)

        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return summary

    def clear_context(self, session_id: str):
        """
        Clear context for a session.

        Args:
            session_id: Session identifier
        """
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.info(f"Cleared context for session: {session_id}")

    def get_context_size(self, session_id: str) -> int:
        """
        Get number of messages in context.

        Args:
            session_id: Session identifier

        Returns:
            Number of messages
        """
        context = self.get_or_create_context(session_id)
        return len(context.messages)
