"""
Pipeline Orchestrator (Simplified)

Simple, focused pipeline: Understand question → Have data? → Answer or suggest alternatives.
"""

import logging
from typing import Dict, Any, List
from anthropic import Anthropic

from .question_classifier import QuestionClassifier
from .response_generator import ResponseGenerator
from .sql_generator import SQLGenerator
from .context_manager import ContextManager
from .exceptions import DataAssistantError

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Simple pipeline orchestrator: Understand → Have data? → Answer or suggest.

    Workflow:
    1. Understand question (with context for follow-ups)
    2. Do we have the data to answer?
       - YES → Generate SQL → Return results
       - NO → Tell user what's missing + suggest alternatives
    3. Remember conversation for next question

    No complexity, just focused answers.
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
            response_generator: Response generator instance
            sql_generator: SQL generator instance
            context_manager: Context manager for conversation memory
        """
        self.classifier = classifier
        self.response_generator = response_generator
        self.sql_generator = sql_generator
        self.context_manager = context_manager
        logger.info("✅ Simplified pipeline orchestrator initialized")

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
                'resolved_question': str
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

                self.context_manager.add_message(
                    session_id=session_id,
                    role='assistant',
                    content=response['explanation']
                )
                return response

            # Step 3: Try to generate SQL from the question
            result = await self.sql_generator.ask(
                question,
                conversation_history=conversation_history
            )

            sql = result.get('sql', '')
            results = result.get('results', [])

            # Check if we could generate SQL
            if not sql:
                # We don't have the data to answer this
                response['explanation'] = self._generate_no_data_response(question, result)
                response['suggestions'] = self._suggest_alternatives(question, result)
                response['success'] = False

                self.context_manager.add_message(
                    session_id=session_id,
                    role='assistant',
                    content=response['explanation']
                )
                return response

            response['sql'] = sql
            response['results'] = results

            # Step 4: Generate simple explanation of results
            explanation = await self.response_generator.generate(
                question=question,
                sql=sql,
                results=results,
                conversation_history=conversation_history
            )
            response['explanation'] = explanation

            # Step 5: Add helpful suggestions if results are empty
            if not results or len(results) == 0:
                response['suggestions'] = self._suggest_alternatives(question, result)

            response['success'] = True

            # Store response in context for follow-up questions
            self.context_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=response['explanation'],
                sql=response['sql'],
                results=response['results']
            )

        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}", exc_info=True)
            response['explanation'] = f"Sorry, I encountered an error: {str(e)}"
            response['success'] = False

            self.context_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=response['explanation']
            )

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
            'resolved_question': ''
        }

    def _generate_no_data_response(self, question: str, result: Dict) -> str:
        """
        Generate friendly response when we don't have the data.

        Args:
            question: User's question
            result: Result from SQL generator

        Returns:
            Friendly explanation of what's missing
        """
        explanation = result.get('explanation', '')

        if explanation:
            return f"I don't have data to answer that. {explanation}"

        return (
            f"I don't have the data needed to answer '{question}'. "
            "The information you're looking for might not be in the database, "
            "or I might need more specific details about what you're looking for."
        )

    def _suggest_alternatives(self, question: str, result: Dict) -> List[str]:
        """
        Suggest helpful alternatives when data is missing or results are empty.

        Args:
            question: User's question
            result: Result from SQL generator

        Returns:
            List of helpful suggestions
        """
        suggestions = []

        # Check if SQL generator provided suggestions
        if 'suggestions' in result and result['suggestions']:
            suggestions.extend(result['suggestions'])

        # Add generic helpful suggestions
        suggestions.extend([
            "Ask 'What tables are available?' to see what data I have",
            "Try rephrasing your question with different terms",
            "Ask about a specific table or column name"
        ])

        return suggestions[:3]  # Keep it simple, max 3 suggestions
