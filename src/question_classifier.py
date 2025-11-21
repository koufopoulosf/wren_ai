"""
Question Classifier

Classifies user questions to determine if they are data queries or meta/system questions.
"""

import logging
import json
from typing import Dict, Any
from anthropic import Anthropic

from llm_utils import LLMUtils
from constants import (
    LLM_MAX_TOKENS_CLASSIFICATION,
    LLM_MAX_TOKENS_CONVERSATIONAL,
    LLM_TEMPERATURE_PRECISE
)
from exceptions import LLMError

logger = logging.getLogger(__name__)


class QuestionClassifier:
    """
    Classifies questions to determine intent and generate appropriate responses.

    This class separates the concern of understanding user intent from
    the actual data query processing logic.
    """

    def __init__(self, anthropic_client: Anthropic, model: str):
        """
        Initialize question classifier.

        Args:
            anthropic_client: Anthropic API client
            model: Claude model name
        """
        self.client = anthropic_client
        self.model = model
        logger.info("✅ Question classifier initialized")

    async def classify(self, question: str) -> Dict[str, Any]:
        """
        Classify whether the question is about data or about the system.

        Args:
            question: User's natural language question

        Returns:
            {
                'is_data_query': bool,
                'response': str (only if not a data query)
            }
        """
        try:
            # Step 1: Classify the question
            classification = await self._classify_question_type(question)

            # Step 2: If it's not a data query, generate a helpful response
            if not classification.get('is_data_query', True):
                response = await self._generate_meta_response(question)
                return {
                    'is_data_query': False,
                    'response': response
                }

            return {'is_data_query': True}

        except LLMError as e:
            logger.warning(f"Question classification failed: {e}, treating as data query")
            # Default to treating as data query to avoid blocking user
            return {'is_data_query': True}

    async def _classify_question_type(self, question: str) -> Dict[str, Any]:
        """
        Internal method to classify question type.

        Args:
            question: User's question

        Returns:
            Classification result with is_data_query flag
        """
        prompt = self._build_classification_prompt(question)

        response_text = await LLMUtils.call_claude_async(
            client=self.client,
            model=self.model,
            prompt=prompt,
            max_tokens=LLM_MAX_TOKENS_CLASSIFICATION,
            temperature=LLM_TEMPERATURE_PRECISE
        )

        # Parse JSON response
        classification = json.loads(response_text)
        logger.info(f"Classification: {classification.get('is_data_query', True)}")

        return classification

    async def _generate_meta_response(self, question: str) -> str:
        """
        Generate response for meta/system questions.

        Args:
            question: User's question about the system

        Returns:
            Helpful response explaining system capabilities
        """
        prompt = self._build_meta_response_prompt(question)

        response = await LLMUtils.call_claude_async(
            client=self.client,
            model=self.model,
            prompt=prompt,
            max_tokens=LLM_MAX_TOKENS_CONVERSATIONAL,
            temperature=LLM_TEMPERATURE_PRECISE
        )

        return response

    @staticmethod
    def _build_classification_prompt(question: str) -> str:
        """
        Build prompt for classifying question type.

        Args:
            question: User's question

        Returns:
            Formatted prompt string
        """
        return f"""Analyze this user question and determine if it's asking about data in a database or if it's a meta/system question.

User question: "{question}"

A DATA QUERY asks about information stored in database tables (tokens, prices, volumes, holdings, transactions, etc.)
Examples of DATA QUERIES:
- "What was Bitcoin's price last month?"
- "Show me top tokens by trading volume"
- "How many active users do we have?"
- "What's the average daily trading volume?"

A META/SYSTEM QUESTION asks about the AI system itself, its capabilities, or is unrelated to the database.
Examples of META/SYSTEM QUESTIONS:
- "Does the AI have access to data?"
- "What can you do?"
- "How does this work?"
- "What tables are available?"
- "Can you help me?"
- "What's the weather?"

Respond with JSON only:
{{
    "is_data_query": true/false,
    "explanation": "brief reason"
}}"""

    @staticmethod
    def _build_meta_response_prompt(question: str) -> str:
        """
        Build prompt for generating meta/system response.

        Args:
            question: User's meta question

        Returns:
            Formatted prompt string
        """
        return f"""You are a helpful AI data assistant for a cryptocurrency trading analytics database.

The user asked: "{question}"

This is a question about the system/capabilities, not a data query. Provide a brief, friendly response.

Available data:
- Cryptocurrency database with tokens, prices, volumes, holdings, transactions
- 2 years of historical OHLCV data (Nov 2023 - Nov 2025)
- 20 major cryptocurrencies (BTC, ETH, USDT, BNB, SOL, ADA, etc.)
- Can answer questions about prices, trading volumes, user holdings, revenue, staking, etc.

Keep your response concise (2-3 sentences) and helpful."""
