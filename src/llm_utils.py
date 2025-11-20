"""
LLM Utility Functions

Provides reusable utilities for interacting with LLM APIs,
eliminating code duplication and centralizing error handling.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from anthropic import Anthropic

from .exceptions import LLMAPIError, LLMResponseError
from .constants import (
    LLM_MAX_TOKENS_SQL_GENERATION,
    LLM_TEMPERATURE_DEFAULT
)

logger = logging.getLogger(__name__)


class LLMUtils:
    """
    Utility class for LLM operations.

    Provides reusable methods for calling LLM APIs with consistent
    error handling and async patterns.
    """

    @staticmethod
    async def call_claude_async(
        client: Anthropic,
        model: str,
        prompt: str,
        max_tokens: int = LLM_MAX_TOKENS_SQL_GENERATION,
        temperature: Optional[float] = None,
        system: Optional[str] = None
    ) -> str:
        """
        Call Claude API asynchronously using event loop executor.

        This method wraps the synchronous Anthropic client in an async
        executor to make it compatible with async/await patterns without
        blocking the event loop.

        Args:
            client: Anthropic API client
            model: Claude model name (e.g., 'claude-sonnet-4-20250514')
            prompt: User prompt/message
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (None uses model default)
            system: Optional system prompt

        Returns:
            Response text from Claude

        Raises:
            LLMAPIError: If API call fails
            LLMResponseError: If response format is invalid
        """
        try:
            # Build message parameters
            params: Dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            }

            # Add optional parameters
            if temperature is not None:
                params["temperature"] = temperature

            if system is not None:
                params["system"] = system

            # Call API using executor to avoid blocking
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: client.messages.create(**params)
            )

            # Extract and validate response
            if not message.content or len(message.content) == 0:
                raise LLMResponseError("Empty response from Claude API")

            response_text = message.content[0].text.strip()

            if not response_text:
                raise LLMResponseError("Response text is empty after stripping")

            logger.debug(f"Claude API call successful: {len(response_text)} chars")
            return response_text

        except LLMResponseError:
            # Re-raise our custom exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Claude API call failed: {e}", exc_info=True)
            raise LLMAPIError(f"Failed to call Claude API: {str(e)}") from e

    @staticmethod
    async def call_claude_with_retry(
        client: Anthropic,
        model: str,
        prompt: str,
        max_tokens: int = LLM_MAX_TOKENS_SQL_GENERATION,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> str:
        """
        Call Claude API with automatic retry on failure.

        Args:
            client: Anthropic API client
            model: Claude model name
            prompt: User prompt/message
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system: Optional system prompt
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            Response text from Claude

        Raises:
            LLMAPIError: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await LLMUtils.call_claude_async(
                    client=client,
                    model=model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system
                )
            except (LLMAPIError, LLMResponseError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.warning(
                        f"Claude API call failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Claude API call failed after {max_retries} attempts")

        # If we get here, all retries failed
        raise LLMAPIError(
            f"Failed after {max_retries} attempts. Last error: {str(last_error)}"
        ) from last_error

    @staticmethod
    def clean_markdown_formatting(text: str) -> str:
        """
        Remove markdown formatting from text.

        Args:
            text: Text potentially containing markdown

        Returns:
            Clean text without markdown formatting
        """
        # Remove bold markers
        text = text.replace('**', '')
        # Remove italic markers
        text = text.replace('*', '')
        # Could add more markdown cleaning as needed
        return text.strip()

    @staticmethod
    def extract_sql_from_markdown(text: str) -> str:
        """
        Extract SQL from markdown code blocks.

        Handles SQL wrapped in ```sql or ``` blocks.

        Args:
            text: Text potentially containing markdown SQL block

        Returns:
            Extracted SQL query
        """
        text = text.strip()

        # Check if wrapped in markdown code block
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```sql or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        return text.strip()
