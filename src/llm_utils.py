"""
LLM Utility Functions

Provides reusable utilities for interacting with LLM APIs,
eliminating code duplication and centralizing error handling.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from anthropic import Anthropic

from exceptions import LLMAPIError, LLMResponseError
from constants import (
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
        system: Optional[str] = None,
        enable_caching: bool = False
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
            enable_caching: Enable prompt caching for the system message (reduces costs by 90% for repeated context)

        Returns:
            Response text from Claude

        Raises:
            LLMAPIError: If API call fails
            LLMResponseError: If response format is invalid
        """
        import time

        logger.info("=" * 80)
        logger.info("LLM UTILS - CALLING CLAUDE API")
        logger.info(f"Model: {model}")
        logger.info(f"Max tokens: {max_tokens}")
        logger.info(f"Temperature: {temperature if temperature is not None else 'default'}")
        logger.info(f"Prompt length: {len(prompt)} chars")
        logger.info(f"Has system prompt: {bool(system)}")
        logger.info(f"Caching enabled: {enable_caching}")
        logger.info("=" * 80)

        start_time = time.time()

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

            # Add system prompt with optional caching
            if system is not None:
                if enable_caching:
                    # Use prompt caching for system message
                    # This marks the schema for caching, reducing costs by 90% on subsequent calls
                    params["system"] = [
                        {
                            "type": "text",
                            "text": system,
                            "cache_control": {"type": "ephemeral"}
                        }
                    ]
                    logger.debug(f"System prompt with caching enabled (length: {len(system)} chars)")
                else:
                    params["system"] = system
                    logger.debug(f"System prompt length: {len(system)} chars")

            # Add caching header if enabled
            extra_headers = {}
            if enable_caching:
                extra_headers["anthropic-beta"] = "prompt-caching-2024-07-31"
                logger.debug("Added prompt caching beta header")

            params["extra_headers"] = extra_headers

            logger.info("Sending request to Claude API...")

            # Call API using executor to avoid blocking
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: client.messages.create(**params)
            )

            elapsed_time = time.time() - start_time

            # Log usage information
            if hasattr(message, 'usage'):
                logger.info(f"API usage - Input tokens: {message.usage.input_tokens}")
                logger.info(f"API usage - Output tokens: {message.usage.output_tokens}")
                total_tokens = message.usage.input_tokens + message.usage.output_tokens
                logger.info(f"API usage - Total tokens: {total_tokens}")

                # Log cache usage if caching is enabled
                if enable_caching and hasattr(message.usage, 'cache_creation_input_tokens'):
                    cache_create = getattr(message.usage, 'cache_creation_input_tokens', 0)
                    cache_read = getattr(message.usage, 'cache_read_input_tokens', 0)
                    if cache_create > 0:
                        logger.info(f"API usage - Cache write tokens: {cache_create} (costs 25% more)")
                    if cache_read > 0:
                        logger.info(f"API usage - Cache read tokens: {cache_read} (costs 10% of normal, 90% savings!)")
                        savings_pct = (cache_read / (cache_read + message.usage.input_tokens)) * 100 if cache_read > 0 else 0
                        logger.info(f"API usage - Cache hit rate: {savings_pct:.1f}%")
            else:
                logger.debug("No usage information available from API response")

            # Extract and validate response
            if not message.content or len(message.content) == 0:
                logger.error("❌ Empty response content from Claude API")
                raise LLMResponseError("Empty response from Claude API")

            response_text = message.content[0].text.strip()

            if not response_text:
                logger.error("❌ Response text is empty after stripping whitespace")
                raise LLMResponseError("Response text is empty after stripping")

            logger.info(f"✅ CLAUDE API CALL SUCCESSFUL in {elapsed_time:.2f}s")
            logger.info(f"Response length: {len(response_text)} chars")
            logger.info("=" * 80)

            return response_text

        except LLMResponseError:
            # Re-raise our custom exceptions as-is
            elapsed_time = time.time() - start_time
            logger.error(f"❌ LLM Response error after {elapsed_time:.2f}s")
            raise
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error("=" * 80)
            logger.error(f"❌ CLAUDE API CALL FAILED after {elapsed_time:.2f}s")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error("=" * 80, exc_info=True)
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
        logger.info(f"LLM UTILS - Calling Claude with retry (max_retries={max_retries})")
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries}")
                result = await LLMUtils.call_claude_async(
                    client=client,
                    model=model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system
                )
                if attempt > 0:
                    logger.info(f"✅ Succeeded on attempt {attempt + 1}/{max_retries}")
                return result

            except (LLMAPIError, LLMResponseError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.warning(
                        f"⚠️ Claude API call failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ Claude API call failed after {max_retries} attempts")

        # If we get here, all retries failed
        logger.error(f"All {max_retries} retry attempts exhausted")
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
