"""
Pipeline Orchestrator (Simplified with Insights)

Simple, focused pipeline: Understand question → Have data? → Answer + Key insights.
"""

import logging
import asyncio
from typing import Dict, Any, List
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
            {
                'success': bool,
                'sql': str,
                'results': List[Dict],
                'explanation': str,
                'suggestions': List[str],
                'resolved_question': str,
                'insights': Dict  # Key takeaways (only if results have 3+ rows)
            }
        """
        response = self._create_empty_response()
        original_question = question

        try:
            # Store user question in context
            self.context_manager.add_message(
                session_id=session_id,
                role='user',
                content=question
            )

            # Step 1: Understand question with context (e.g., "show me more" → "show me more Bitcoin prices")
            resolved_question = await self.context_manager.resolve_references(
                question=question,
                session_id=session_id
            )
            question = resolved_question
            response['resolved_question'] = resolved_question

            if resolved_question != original_question:
                logger.info(f"📝 Resolved: '{original_question}' → '{resolved_question}'")

            # Step 2: Classify question (data query vs. meta question like "what can you do?")
            classification = await self.classifier.classify(question)

            if not classification.get('is_data_query', True):
                # Meta query - return conversational response
                response['success'] = True
                response['explanation'] = classification.get('response', '')
                self._store_assistant_response(session_id, response['explanation'])
                return response

            # Step 3: Try to generate SQL from the question
            sql_result = await self.sql_generator.ask(
                question,
                conversation_history=conversation_history
            )

            sql = sql_result.get('sql', '')
            results = sql_result.get('results', [])

            # Check if we could generate SQL
            if not sql:
                # We don't have the data to answer this
                response['explanation'] = self._generate_no_data_response(question, sql_result)
                response['suggestions'] = self._suggest_alternatives(question, sql_result)
                response['success'] = False
                self._store_assistant_response(session_id, response['explanation'])
                return response

            response['sql'] = sql
            response['results'] = results

            # Step 4: Generate explanation + insights in parallel (if we have meaningful data)
            if results and len(results) >= MIN_RESULTS_FOR_INSIGHTS:
                # Both need same inputs, so run in parallel for speed!
                explanation_task = self.response_generator.generate(
                    question=question,
                    sql=sql,
                    results=results,
                    conversation_history=conversation_history
                )

                insights_task = self.insight_generator.generate_insights(
                    question=question,
                    sql=sql,
                    results=results
                )

                # Run both at the same time
                explanation, insights = await asyncio.gather(
                    explanation_task,
                    insights_task
                )

                response['explanation'] = explanation
                response['insights'] = insights.to_dict()

                # Add insight summary to suggestions if available
                if insights.has_insights() and insights.summary:
                    response['suggestions'].insert(0, f"💡 {insights.summary}")
            else:
                # Just explanation for empty results or small datasets
                explanation = await self.response_generator.generate(
                    question=question,
                    sql=sql,
                    results=results,
                    conversation_history=conversation_history
                )
                response['explanation'] = explanation
                response['insights'] = None

            # Step 5: Add helpful suggestions if results are empty
            if not results or len(results) == 0:
                response['suggestions'] = self._suggest_alternatives(question, sql_result)

            response['success'] = True

            # Store response in context for follow-up questions
            self._store_assistant_response_with_data(
                session_id=session_id,
                explanation=response['explanation'],
                sql=response['sql'],
                results=response['results']
            )

        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}", exc_info=True)
            response['explanation'] = f"Sorry, I encountered an error: {str(e)}"
            response['success'] = False
            self._store_assistant_response(session_id, response['explanation'])

        return response

    @staticmethod
    def _create_empty_response() -> Dict[str, Any]:
        """Create simple response structure."""
        return {
            'success': False,
            'sql': '',
            'results': [],
            'explanation': '',
            'suggestions': [],
            'resolved_question': '',
            'insights': None
        }

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
