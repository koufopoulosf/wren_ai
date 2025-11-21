"""
Response Generator

Generates conversational responses for query results.
"""

import logging
import json
from typing import List, Dict, Any
from anthropic import Anthropic

from llm_utils import LLMUtils
from constants import (
    LLM_MAX_TOKENS_CONVERSATIONAL,
    LLM_TEMPERATURE_PRECISE
)
from exceptions import LLMError

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

    async def generate_with_insights(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive response with explanation and key insights in ONE LLM call.

        This consolidates what used to be separate response_generator and insight_generator calls.

        Args:
            question: User's original question
            sql: Generated SQL query
            results: Query results (may be empty)
            conversation_history: Previous conversation messages

        Returns:
            Dictionary with:
            {
                'explanation': str,  # Natural language explanation
                'insights': {        # Key takeaways
                    'summary': str,
                    'top_findings': List[str],
                    'trends': List[str],
                    'outliers': List[str],
                    'recommendations': List[str]
                }
            }
        """
        try:
            # Build the unified prompt
            prompt = self._build_unified_prompt(
                question=question,
                sql=sql,
                results=results,
                conversation_history=conversation_history
            )

            # Generate response
            response_text = await LLMUtils.call_claude_async(
                client=self.client,
                model=self.model,
                prompt=prompt,
                max_tokens=LLM_MAX_TOKENS_CONVERSATIONAL,
                temperature=LLM_TEMPERATURE_PRECISE
            )

            # Parse structured response
            try:
                # Try to parse as JSON
                response_data = json.loads(response_text)

                # Validate structure
                if 'explanation' not in response_data:
                    # Fallback: treat entire response as explanation
                    return {
                        'explanation': response_text.strip(),
                        'insights': {}
                    }

                return response_data

            except json.JSONDecodeError:
                # Fallback: treat as plain text explanation
                logger.warning("Could not parse structured response, using as plain text")
                return {
                    'explanation': response_text.strip(),
                    'insights': {}
                }

        except LLMError as e:
            logger.error(f"Error generating unified response: {e}")
            # Fallback to simple response
            return {
                'explanation': self._generate_fallback_response(results),
                'insights': {}
            }

    def _build_unified_prompt(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        conversation_history: list = None
    ) -> str:
        """
        Build prompt for generating unified response with explanation and insights.

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

        # Format actual results data for the LLM to see
        results_data = self._format_results_for_prompt(results)

        # Build prompt
        prompt = f"""You are a helpful AI data assistant for a cryptocurrency trading analytics database.

## User's Question
{question}

## SQL Query Generated
```sql
{sql}
```

## Actual Query Results
{results_data}
{conversation_context}

## Your Task
Analyze the data and provide a comprehensive response in JSON format with two parts:

1. **explanation**: A natural, conversational 2-4 sentence explanation that directly answers the question using the actual data
2. **insights**: Key takeaways from the data (only if results exist and are meaningful)

### Response Format
Return ONLY valid JSON in this exact structure:
```json
{{
  "explanation": "Your conversational explanation here, using specific values from the data",
  "insights": {{
    "summary": "One sentence summarizing the most important finding (optional)",
    "top_findings": ["Notable fact 1", "Notable fact 2"],
    "trends": ["Pattern or trend observed"],
    "outliers": ["Unusual values or anomalies"],
    "recommendations": ["Suggested next steps or related queries"]
  }}
}}
```

### Guidelines for "explanation":
- Answer the question directly using ACTUAL values from the results
- Be specific with numbers and values
- Sound conversational, like a helpful colleague
- Keep it concise (2-4 sentences)

### Guidelines for "insights":
- Only include if there are meaningful results (skip for empty results or single values)
- top_findings: 2-3 most notable data points
- trends: Patterns you notice in the data
- outliers: Unusual or surprising values
- recommendations: What the user might want to explore next
- Leave arrays empty [] if no meaningful insights exist

### Examples

For "What was Bitcoin's highest price in 2024?":
```json
{{
  "explanation": "Bitcoin's highest price in 2024 was $73,750.50, which represents a significant peak in the market cycle.",
  "insights": {{
    "summary": "Bitcoin reached an all-time high in 2024",
    "top_findings": ["Peak price of $73,750.50 in 2024", "This represents a 156% increase from 2023's high"],
    "trends": [],
    "outliers": [],
    "recommendations": ["Check monthly price trends to see when the peak occurred", "Compare with Ethereum's 2024 performance"]
  }}
}}
```

For "Show top 5 tokens by volume":
```json
{{
  "explanation": "Here are the top 5 tokens by trading volume. Bitcoin leads with $2.4B, followed by Ethereum at $1.8B, and Tether at $1.2B.",
  "insights": {{
    "summary": "Bitcoin and Ethereum dominate trading volume",
    "top_findings": ["Bitcoin has 33% more volume than Ethereum", "Top 3 tokens account for 68% of total volume"],
    "trends": ["Stablecoins (Tether) showing strong trading activity"],
    "outliers": [],
    "recommendations": ["Analyze volume trends over time", "Check if high volume correlates with price movements"]
  }}
}}
```

For empty results:
```json
{{
  "explanation": "I couldn't find any data matching those criteria. This could mean no activity occurred during that period, or the token name might need different capitalization. Try searching for 'Bitcoin' or 'Ethereum' instead.",
  "insights": {{}}
}}
```

IMPORTANT:
- Return ONLY the JSON object, no additional text
- Use the ACTUAL data from "Actual Query Results" above
- Do not make up or guess values
- If results are empty or have only 1 simple value, keep insights minimal or empty

Generate your JSON response:"""

        return prompt

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
        Build prompt for generating conversational response with actual data.

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

        # Format actual results data for the LLM to see
        results_data = self._format_results_for_prompt(results)

        # Build prompt
        prompt = f"""You are a helpful AI data assistant for a cryptocurrency trading analytics database. Generate a conversational response for the user.

## User's Question
{question}

## SQL Query Generated
```sql
{sql}
```

## Actual Query Results
{results_data}
{conversation_context}

## Your Task
Generate a natural, conversational response that:

1. **Answers the question directly** using the ACTUAL data shown above
2. **Highlights key findings** if there's interesting data (e.g., highest/lowest values, trends, notable facts)
3. **Be specific** - use the actual numbers and values from the results
4. **Be conversational** - sound like a helpful colleague explaining data, not a robot
5. **Keep it concise** - 2-4 sentences maximum

Examples of GOOD responses (with real data):
- "Bitcoin's highest price in 2024 was $73,750.50, which occurred in March during the market rally."
- "I found 25 tokens in the database. Bitcoin is the most held with 1,234 holdings, followed by Ethereum with 987 holdings."
- "No transactions match those criteria. This could mean no activity occurred during that period, or the token name might be different. Try searching for 'Ethereum' or 'Bitcoin' instead."

Examples of BAD responses:
- "The query returned results but I can't see the actual values." (WRONG - you CAN see the data above!)
- "The query executed successfully." (too technical, not conversational)
- "Here are the results:" (not helpful, not answering the question)

IMPORTANT: Base your response on the ACTUAL data shown in the "Actual Query Results" section above. Do not make up or guess values.

Generate your response:"""

        return prompt

    @staticmethod
    def _format_results_for_prompt(results: List[Dict], max_rows: int = 10) -> str:
        """
        Format query results for inclusion in LLM prompt.

        Args:
            results: Query results to format
            max_rows: Maximum number of rows to include (default 10)

        Returns:
            Formatted string representation of results
        """
        if not results or len(results) == 0:
            return "No results returned (empty result set)"

        import json

        # Limit rows to avoid overwhelming the context
        display_results = results[:max_rows]
        has_more = len(results) > max_rows

        # Format as clean JSON
        formatted = json.dumps(display_results, indent=2, default=str)

        result_text = f"{len(results)} row(s) returned:\n{formatted}"

        if has_more:
            result_text += f"\n\n(Showing first {max_rows} of {len(results)} total rows)"

        return result_text

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
