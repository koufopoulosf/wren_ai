"""
Pipeline Orchestrator (Simplified)

Simple, focused pipeline: Understand question → Have data? → Answer + Optional insights.
"""

import logging
import asyncio
import hashlib
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from anthropic import Anthropic

from question_classifier import QuestionClassifier
from response_generator import ResponseGenerator
from sql_generator import SQLGenerator
from context_manager import ContextManager
from exceptions import DataAssistantError
from constants import (
    MIN_RESULTS_FOR_INSIGHTS,
    DEFAULT_NO_DATA_SUGGESTIONS,
    MAX_SUGGESTIONS_TO_SHOW
)

logger = logging.getLogger(__name__)


@dataclass
class QueryResponse:
    """
    Type-safe response structure for pipeline queries.

    Using a dataclass provides:
    - Type hints and IDE autocomplete
    - Catches typos at design time
    - Clear documentation of response structure
    """
    success: bool = False
    sql: str = ''
    results: List[Dict] = field(default_factory=list)
    explanation: str = ''
    suggestions: List[str] = field(default_factory=list)
    resolved_question: str = ''
    insights: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            'success': self.success,
            'sql': self.sql,
            'results': self.results,
            'explanation': self.explanation,
            'suggestions': self.suggestions,
            'resolved_question': self.resolved_question,
            'insights': self.insights
        }


class PipelineOrchestrator:
    """
    Simple pipeline orchestrator: Understand → Have data? → Answer + Optional insights.

    Workflow:
    1. Understand question (with context for follow-ups)
    2. Do we have the data to answer?
       - YES → Generate SQL → Return results + explanation
       - NO → Tell user what's missing + suggest alternatives
    3. Remember conversation for next question

    Insights are generated on-demand when user clicks "Show Key Takeaways" button.
    """

    def __init__(
        self,
        classifier: QuestionClassifier,
        response_generator: ResponseGenerator,
        sql_generator: SQLGenerator,
        context_manager: ContextManager
    ):
        """
        Initialize simplified pipeline orchestrator.

        Args:
            classifier: Question classifier instance
            response_generator: Response generator instance (includes insights generation)
            sql_generator: SQL generator instance
            context_manager: Context manager for conversation memory
        """
        self.classifier = classifier
        self.response_generator = response_generator
        self.sql_generator = sql_generator
        self.context_manager = context_manager

        # Results cache: {cache_key: (results, timestamp)}
        self._results_cache = {}
        self._cache_ttl = 300  # 5 minutes

        logger.info("✅ Simplified pipeline orchestrator initialized with results caching")

    def _get_cache_key(self, question: str, session_id: str) -> str:
        """Generate cache key for a query."""
        combined = f"{session_id}:{question.lower().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """Check if results are cached and still valid."""
        if cache_key in self._results_cache:
            cached_data, timestamp = self._results_cache[cache_key]
            age = time.time() - timestamp
            if age < self._cache_ttl:
                logger.info(f"✅ Cache HIT! (age: {age:.1f}s, TTL: {self._cache_ttl}s) - Instant response!")
                return cached_data
            else:
                logger.debug(f"Cache expired (age: {age:.1f}s > TTL: {self._cache_ttl}s)")
                del self._results_cache[cache_key]
        return None

    def _store_in_cache(self, cache_key: str, data: Dict) -> None:
        """Store results in cache."""
        self._results_cache[cache_key] = (data, time.time())
        logger.debug(f"📦 Stored in cache (total cached queries: {len(self._results_cache)})")

    def _generate_template_response(self, results: List[Dict], question: str) -> Optional[str]:
        """
        Generate fast template-based response for simple queries.
        Returns None if template doesn't apply.
        """
        if not results:
            return None

        num_results = len(results)

        # Single value result (e.g., MAX, MIN, COUNT, SUM, AVG)
        if num_results == 1 and len(results[0]) == 1:
            key = list(results[0].keys())[0]
            value = results[0][key]

            # Format the value nicely
            if isinstance(value, (int, float)):
                if value > 1000000:
                    formatted = f"${value:,.2f}" if 'price' in key.lower() or 'usd' in key.lower() or 'volume' in key.lower() else f"{value:,.0f}"
                else:
                    formatted = f"${value:,.2f}" if 'price' in key.lower() or 'usd' in key.lower() else f"{value:,.0f}"
            else:
                formatted = str(value)

            logger.info("⚡ Using template response for single-value result (instant!)")
            return f"The result is **{formatted}**."

        # Top N results (common pattern)
        if num_results <= 10 and num_results > 0:
            first_row = results[0]
            if len(first_row) >= 2:
                # Assume first column is name/label, second is value
                cols = list(first_row.keys())
                name_col, value_col = cols[0], cols[1]

                top_item = results[0]
                top_name = top_item[name_col]
                top_value = top_item[value_col]

                logger.info(f"⚡ Using template response for top-N results (instant!)")
                if isinstance(top_value, (int, float)):
                    formatted_val = f"${top_value:,.2f}" if 'usd' in value_col.lower() or 'price' in value_col.lower() else f"{top_value:,.0f}"
                else:
                    formatted_val = str(top_value)

                return f"Found {num_results} results. Top result: **{top_name}** with {formatted_val}."

        return None

    async def process(
        self,
        question: str,
        session_id: str = "default",
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        Process user question through simplified pipeline.

        Args:
            question: User's natural language question
            session_id: Session identifier for context management
            conversation_history: List of previous messages for context

        Returns:
            Dictionary representation of QueryResponse
        """
        logger.info("=" * 80)
        logger.info("PIPELINE ORCHESTRATOR - PROCESSING NEW QUESTION")
        logger.info(f"Question: {question}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"History length: {len(conversation_history) if conversation_history else 0}")
        logger.info("=" * 80)

        response = QueryResponse()
        start_time = datetime.now()

        try:
            # Check cache first
            cache_key = self._get_cache_key(question, session_id)
            cached_result = self._check_cache(cache_key)
            if cached_result:
                logger.info("📦 Returning cached result (instant response!)")
                return cached_result

            # Store user question in context
            logger.debug(f"Storing user question in context manager (session: {session_id})")
            self.context_manager.add_message(
                session_id=session_id,
                role='user',
                content=question
            )
            logger.debug("✅ User question stored in context")

            # Step 1: Resolve references only (skip expensive classification)
            logger.info("STEP 1: Resolving references...")
            step_start = datetime.now()

            resolved_question = await self.context_manager.resolve_references(
                question=question,
                session_id=session_id
            )
            response.resolved_question = resolved_question

            if resolved_question != question:
                logger.info(f"📝 Resolved: '{question}' → '{resolved_question}'")

            step_elapsed = (datetime.now() - step_start).total_seconds()
            logger.info(f"✅ STEP 1 completed in {step_elapsed:.2f}s")
            logger.info(f"Resolved question: {resolved_question}")

            # Step 2: Generate SQL and execute (classification removed for speed)
            logger.info("STEP 2: Generating and executing SQL...")
            step_start = datetime.now()

            sql_result = await self._generate_sql_and_results(
                resolved_question, conversation_history
            )

            step_elapsed = (datetime.now() - step_start).total_seconds()
            logger.info(f"✅ STEP 2 completed in {step_elapsed:.2f}s")
            logger.info(f"SQL generated: {bool(sql_result.get('sql', ''))}")
            logger.info(f"Results count: {len(sql_result.get('results', []))}")

            # Handle case where we don't have the data
            if not sql_result.get('sql', ''):
                logger.warning("⚠️ No SQL generated - missing required data")
                result = self._handle_no_data_found(
                    response, resolved_question, sql_result, session_id
                ).to_dict()
                total_elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ Pipeline completed in {total_elapsed:.2f}s (no data)")
                return result

            # Step 3: Generate response explanation (try template first, then LLM)
            logger.info("STEP 3: Generating response explanation...")
            step_start = datetime.now()

            # Try fast template-based response first
            template_response = self._generate_template_response(
                sql_result.get('results', []),
                resolved_question
            )

            if template_response:
                # Template worked! Super fast response
                response.sql = sql_result.get('sql', '')
                response.results = sql_result.get('results', [])
                response.explanation = template_response
                step_elapsed = (datetime.now() - step_start).total_seconds()
                logger.info(f"✅ STEP 3 completed in {step_elapsed:.2f}s (template)")
            else:
                # Fall back to LLM for complex responses
                response = await self._generate_response_explanation_only(
                    response, resolved_question, sql_result, conversation_history
                )
                step_elapsed = (datetime.now() - step_start).total_seconds()
                logger.info(f"✅ STEP 3 completed in {step_elapsed:.2f}s (LLM)")

            logger.info(f"Explanation length: {len(response.explanation)} chars")

            response.success = True

            # Store in context
            logger.debug("Storing assistant response with data in context")
            self._store_assistant_response_with_data(
                session_id=session_id,
                explanation=response.explanation,
                sql=response.sql,
                results=response.results
            )

            total_elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ PIPELINE COMPLETED SUCCESSFULLY in {total_elapsed:.2f}s")
            logger.info("=" * 80)

            # Store in cache for future requests
            result_dict = response.to_dict()
            self._store_in_cache(cache_key, result_dict)

        except Exception as e:
            total_elapsed = (datetime.now() - start_time).total_seconds()
            logger.error("=" * 80)
            logger.error(f"❌ PIPELINE ERROR after {total_elapsed:.2f}s")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error("=" * 80, exc_info=True)

            response.explanation = f"Sorry, I encountered an error: {str(e)}"
            response.success = False
            self._store_assistant_response(session_id, response.explanation)

        return response.to_dict()


    async def _generate_sql_and_results(
        self,
        question: str,
        conversation_history: list
    ) -> Dict:
        """
        Generate SQL from question and execute it.

        Args:
            question: Resolved question
            conversation_history: Conversation context

        Returns:
            SQL generation result with sql, results, and suggestions
        """
        return await self.sql_generator.ask(
            question,
            conversation_history=conversation_history
        )

    def _handle_no_data_found(
        self,
        response: QueryResponse,
        question: str,
        sql_result: Dict,
        session_id: str
    ) -> QueryResponse:
        """
        Handle case where we don't have data to answer the question.

        Args:
            response: Response object to populate
            question: User's question
            sql_result: SQL generation result
            session_id: Session identifier

        Returns:
            Populated QueryResponse
        """
        response.explanation = self._generate_no_data_response(question, sql_result)
        response.suggestions = self._suggest_alternatives(question, sql_result)
        response.success = False
        self._store_assistant_response(session_id, response.explanation)
        return response

    async def _generate_response_explanation_only(
        self,
        response: QueryResponse,
        question: str,
        sql_result: Dict,
        conversation_history: list
    ) -> QueryResponse:
        """
        Generate ONLY explanation (no insights).

        This is faster and more cost-effective. Users can request insights separately
        via action buttons in the UI.

        Args:
            response: Response object to populate
            question: User's question
            sql_result: SQL generation result
            conversation_history: Conversation context

        Returns:
            Populated QueryResponse (without insights)
        """
        sql = sql_result.get('sql', '')
        results = sql_result.get('results', [])

        response.sql = sql
        response.results = results

        # Generate explanation ONLY (no insights)
        response.explanation = await self.response_generator.generate_explanation_only(
            question=question,
            sql=sql,
            results=results,
            conversation_history=conversation_history
        )

        # Add suggestions for empty results
        if not results:
            response.suggestions = self._suggest_alternatives(question, sql_result)

        return response

    async def generate_insights_for_response(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        Generate insights on-demand for an existing response.

        This is called when user clicks "Show Key Takeaways & Recommendations" button.

        Args:
            question: User's original question
            sql: SQL query that was executed
            results: Query results
            conversation_history: Conversation context

        Returns:
            Dictionary with insights (summary, top_findings, trends, outliers, recommendations)
        """
        return await self.response_generator.generate_insights_only(
            question=question,
            sql=sql,
            results=results,
            conversation_history=conversation_history
        )

    def _generate_no_data_response(self, question: str, sql_result: Dict) -> str:
        """
        Generate friendly response when we don't have the data.

        Args:
            question: User's question
            sql_result: Result from SQL generator

        Returns:
            Friendly explanation of what's missing
        """
        explanation = sql_result.get('explanation', '')

        if explanation:
            return f"I don't have data to answer that. {explanation}"

        return (
            f"I don't have the data needed to answer '{question}'. "
            "The information you're looking for might not be in the database, "
            "or I might need more specific details about what you're looking for."
        )

    def _suggest_alternatives(self, question: str, sql_result: Dict) -> List[str]:
        """
        Suggest helpful alternatives when data is missing or results are empty.

        Args:
            question: User's question
            sql_result: Result from SQL generator

        Returns:
            List of helpful suggestions
        """
        suggestions = []

        # Check if SQL generator provided suggestions
        if 'suggestions' in sql_result and sql_result['suggestions']:
            suggestions.extend(sql_result['suggestions'])

        # Add generic helpful suggestions from constants
        suggestions.extend(DEFAULT_NO_DATA_SUGGESTIONS)

        return suggestions[:MAX_SUGGESTIONS_TO_SHOW]

    def _store_assistant_response(self, session_id: str, content: str) -> None:
        """
        Store simple assistant response in context (for meta queries and errors).

        Args:
            session_id: Session identifier
            content: Response text to store
        """
        self.context_manager.add_message(
            session_id=session_id,
            role='assistant',
            content=content
        )

    def _store_assistant_response_with_data(
        self,
        session_id: str,
        explanation: str,
        sql: str,
        results: List[Dict]
    ) -> None:
        """
        Store assistant response with SQL and results in context.

        Args:
            session_id: Session identifier
            explanation: Response explanation
            sql: SQL query that was executed
            results: Query results
        """
        self.context_manager.add_message(
            session_id=session_id,
            role='assistant',
            content=explanation,
            sql=sql,
            results=results
        )
