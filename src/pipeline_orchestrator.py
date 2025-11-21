"""
Pipeline Orchestrator (Simplified with Insights)

Simple, focused pipeline: Understand question → Have data? → Answer + Key insights.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from anthropic import Anthropic

from .question_classifier import QuestionClassifier
from .response_generator import ResponseGenerator
from .sql_generator import SQLGenerator
from .context_manager import ContextManager
from .insight_generator import InsightGenerator
from .exceptions import DataAssistantError
from .constants import (
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
    Simple pipeline orchestrator: Understand → Have data? → Answer + Insights.

    Workflow:
    1. Understand question (with context for follow-ups)
    2. Do we have the data to answer?
       - YES → Generate SQL → Return results + insights (parallel)
       - NO → Tell user what's missing + suggest alternatives
    3. Remember conversation for next question

    Insights run in parallel with response generation for speed.
    """

    def __init__(
        self,
        classifier: QuestionClassifier,
        response_generator: ResponseGenerator,
        sql_generator: SQLGenerator,
        context_manager: ContextManager,
        insight_generator: InsightGenerator
    ):
        """
        Initialize simplified pipeline orchestrator with insights.

        Args:
            classifier: Question classifier instance
            response_generator: Response generator instance
            sql_generator: SQL generator instance
            context_manager: Context manager for conversation memory
            insight_generator: Insight generator for key takeaways
        """
        self.classifier = classifier
        self.response_generator = response_generator
        self.sql_generator = sql_generator
        self.context_manager = context_manager
        self.insight_generator = insight_generator
        logger.info("✅ Simplified pipeline orchestrator initialized with insights")

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
        response = QueryResponse()

        try:
            # Store user question in context
            self.context_manager.add_message(
                session_id=session_id,
                role='user',
                content=question
            )

            # Step 1 & 2: Resolve references and classify question
            resolved_question, classification = await self._resolve_and_classify_question(
                question, session_id
            )
            response.resolved_question = resolved_question

            # Handle meta queries (non-data questions)
            if not classification.get('is_data_query', True):
                return self._handle_meta_query(
                    response, classification, session_id
                ).to_dict()

            # Step 3: Generate SQL and execute
            sql_result = await self._generate_sql_and_results(
                resolved_question, conversation_history
            )

            # Handle case where we don't have the data
            if not sql_result.get('sql', ''):
                return self._handle_no_data_found(
                    response, resolved_question, sql_result, session_id
                ).to_dict()

            # Step 4 & 5: Generate response with insights
            response = await self._generate_response_with_insights(
                response, resolved_question, sql_result, conversation_history
            )

            response.success = True

            # Store in context
            self._store_assistant_response_with_data(
                session_id=session_id,
                explanation=response.explanation,
                sql=response.sql,
                results=response.results
            )

        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}", exc_info=True)
            response.explanation = f"Sorry, I encountered an error: {str(e)}"
            response.success = False
            self._store_assistant_response(session_id, response.explanation)

        return response.to_dict()

    async def _resolve_and_classify_question(
        self, question: str, session_id: str
    ) -> tuple[str, Dict]:
        """
        Resolve question references and classify question type.

        Args:
            question: User's question
            session_id: Session identifier

        Returns:
            Tuple of (resolved_question, classification)
        """
        # Resolve references using context (e.g., "show me more" → "show me more Bitcoin prices")
        resolved_question = await self.context_manager.resolve_references(
            question=question,
            session_id=session_id
        )

        if resolved_question != question:
            logger.info(f"📝 Resolved: '{question}' → '{resolved_question}'")

        # Classify question (data query vs. meta question)
        classification = await self.classifier.classify(resolved_question)

        return resolved_question, classification

    def _handle_meta_query(
        self,
        response: QueryResponse,
        classification: Dict,
        session_id: str
    ) -> QueryResponse:
        """
        Handle non-data queries (e.g., "what can you do?").

        Args:
            response: Response object to populate
            classification: Classification result
            session_id: Session identifier

        Returns:
            Populated QueryResponse
        """
        response.success = True
        response.explanation = classification.get('response', '')
        self._store_assistant_response(session_id, response.explanation)
        return response

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

    async def _generate_response_with_insights(
        self,
        response: QueryResponse,
        question: str,
        sql_result: Dict,
        conversation_history: list
    ) -> QueryResponse:
        """
        Generate explanation and insights (in parallel when possible).

        Args:
            response: Response object to populate
            question: User's question
            sql_result: SQL generation result
            conversation_history: Conversation context

        Returns:
            Populated QueryResponse
        """
        sql = sql_result.get('sql', '')
        results = sql_result.get('results', [])

        response.sql = sql
        response.results = results

        # Generate insights in parallel if we have meaningful data
        if results and len(results) >= MIN_RESULTS_FOR_INSIGHTS:
            explanation, insights = await asyncio.gather(
                self.response_generator.generate(
                    question=question,
                    sql=sql,
                    results=results,
                    conversation_history=conversation_history
                ),
                self.insight_generator.generate_insights(
                    question=question,
                    sql=sql,
                    results=results
                )
            )

            response.explanation = explanation
            response.insights = insights.to_dict()

            # Add insight summary to suggestions
            if insights.has_insights() and insights.summary:
                response.suggestions.insert(0, f"💡 {insights.summary}")
        else:
            # Just explanation for empty/small datasets
            response.explanation = await self.response_generator.generate(
                question=question,
                sql=sql,
                results=results,
                conversation_history=conversation_history
            )

        # Add suggestions for empty results
        if not results:
            response.suggestions = self._suggest_alternatives(question, sql_result)

        return response

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
