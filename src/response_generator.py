"""
Response Generator

Generates conversational responses for query results.
"""

import logging
from typing import List, Dict, Any
from anthropic import Anthropic

from .llm_utils import LLMUtils
from .constants import (
    LLM_MAX_TOKENS_CONVERSATIONAL,
    LLM_TEMPERATURE_PRECISE
)
from .exceptions import LLMError

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generates natural, conversational responses for query results.

    This class focuses solely on creating user-friendly explanations
    of SQL query results, especially handling edge cases like empty results.
    """

    def __init__(self, anthropic_client: Anthropic, model: str):
        """
        Initialize response generator.

        Args:
            anthropic_client: Anthropic API client
            model: Claude model name
        """
        self.client = anthropic_client
        self.model = model
        logger.info("✅ Response generator initialized")

    async def generate(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        conversation_history: list = None
    ) -> str:
        """
        Generate a conversational response for query results.

        Args:
            question: User's original question
            sql: Generated SQL query
            results: Query results (may be empty)
            conversation_history: Previous conversation messages

        Returns:
            Conversational response string
        """
        try:
            # Build the prompt
            prompt = self._build_response_prompt(
                question=question,
                sql=sql,
                results=results,
                conversation_history=conversation_history
            )

            # Generate response
            response = await LLMUtils.call_claude_async(
                client=self.client,
                model=self.model,
                prompt=prompt,
                max_tokens=LLM_MAX_TOKENS_CONVERSATIONAL,
                temperature=LLM_TEMPERATURE_PRECISE
            )

            return response

        except LLMError as e:
            logger.error(f"Error generating conversational response: {e}")
            # Fallback to simple response
            return self._generate_fallback_response(results)

    def _build_response_prompt(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        conversation_history: list = None
    ) -> str:
        """
        Build prompt for generating conversational response.

        Args:
            question: User's question
            sql: SQL query
            results: Query results
            conversation_history: Conversation context

        Returns:
            Formatted prompt string
        """
        # Build conversation context
        conversation_context = self._build_conversation_context(conversation_history)

        # Check if results are empty
        is_empty = not results or len(results) == 0

        # Build prompt
        prompt = f"""You are a helpful AI data assistant for a cryptocurrency trading analytics database. Generate a conversational response for the user.

## User's Question
{question}

## SQL Query Generated
```sql
{sql}
```

## Query Results
{"No results returned (empty result set)" if is_empty else f"{len(results)} rows returned"}
{conversation_context}

## Your Task
{"The query returned NO results. Generate a helpful, conversational response that:" if is_empty else "The query returned results. Generate a brief, natural explanation that:"}

1. **Explains the situation** in natural language (why no data was found OR what the results show)
2. **Suggests alternatives** if no data found:
   - Check if the user might have meant something else
   - Suggest related queries they could try
   - Ask clarifying questions if the request was ambiguous
3. **Be conversational** - sound like a helpful colleague, not a robot
4. **Keep it concise** - 2-4 sentences maximum

Examples of GOOD responses:
- "I don't have any data about token hunts in the database. Did you perhaps mean 'token holdings' or 'token transactions'? I can show you which tokens users hold most frequently if that helps."
- "I couldn't find any records matching that criteria. This could mean either no data exists for that time period, or the column name might be different. Could you clarify what you're looking for?"
- "The query found 25 tokens and their holding counts. Bitcoin is the most held token with 1,234 holdings, followed by Ethereum with 987 holdings."

Examples of BAD responses:
- "The query executed successfully but returned no rows." (too technical)
- "No data found." (not helpful)
- "Here are the results:" (not conversational)

Generate your response:"""

        return prompt

    @staticmethod
    def _build_conversation_context(conversation_history: list = None) -> str:
        """
        Build conversation context from history.

        Args:
            conversation_history: List of previous messages

        Returns:
            Formatted conversation context string
        """
        if not conversation_history or len(conversation_history) == 0:
            return ""

        # Get last 3 messages for context
        recent_history = conversation_history[-3:]
        history_parts = []

        for msg in recent_history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            # Truncate long messages
            if len(content) > 200:
                content = content[:200] + "..."

            history_parts.append(f"{role.capitalize()}: {content}")

        return f"""

## Recent Conversation History
{chr(10).join(history_parts)}
"""

    @staticmethod
    def _generate_fallback_response(results: List[Dict]) -> str:
        """
        Generate simple fallback response if LLM fails.

        Args:
            results: Query results

        Returns:
            Simple fallback message
        """
        if not results or len(results) == 0:
            return "I couldn't find any data matching your question. Could you rephrase or provide more details about what you're looking for?"
        else:
            return f"Found {len(results)} results."
