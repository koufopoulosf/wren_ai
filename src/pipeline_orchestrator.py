"""
Pipeline Orchestrator

Orchestrates the query processing pipeline from question to results.
"""

import logging
from typing import Dict, Any, List
from anthropic import Anthropic

from .question_classifier import QuestionClassifier
from .response_generator import ResponseGenerator
from .sql_generator import SQLGenerator
from .result_validator import ResultValidator
from .context_manager import ContextManager
from .exceptions import DataAssistantError

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates the complete query processing pipeline with context management.

    This class coordinates the workflow:
    1. Resolve references in question using context
    2. Classify the question
    3. Generate SQL if it's a data query
    4. Execute and validate results
    5. Generate conversational response
    6. Store results in context for future reference

    Single Responsibility: Pipeline coordination and workflow management
    """

    def __init__(
        self,
        classifier: QuestionClassifier,
        response_generator: ResponseGenerator,
        sql_generator: SQLGenerator,
        result_validator: ResultValidator,
        context_manager: ContextManager
    ):
        """
        Initialize pipeline orchestrator.

        Args:
            classifier: Question classifier instance
            response_generator: Response generator instance
            sql_generator: SQL generator instance
            result_validator: Result validator instance
            context_manager: Context manager for conversation memory
        """
        self.classifier = classifier
        self.response_generator = response_generator
        self.sql_generator = sql_generator
        self.result_validator = result_validator
        self.context_manager = context_manager
        logger.info("✅ Pipeline orchestrator initialized with context manager")

    async def process(
        self,
        question: str,
        session_id: str = "default",
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        Process user question through the complete pipeline with context management.

        Args:
            question: User's natural language question
            session_id: Session identifier for context management
            conversation_history: List of previous messages for context (deprecated, use context manager)

        Returns:
            {
                'success': bool,
                'sql': str,
                'results': List[Dict],
                'explanation': str,
                'warnings': List[str],
                'suggestions': List[str],
                'confidence': float,
                'resolved_question': str  # Question after reference resolution
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

            # Step 1: Resolve references using context ("show me more" → "show me more Bitcoin prices")
            resolved_question = await self.context_manager.resolve_references(
                question=question,
                session_id=session_id
            )

            # Use resolved question for processing
            question = resolved_question
            response['resolved_question'] = resolved_question

            if resolved_question != original_question:
                logger.info(f"Resolved reference: '{original_question}' → '{resolved_question}'")

            # Step 2: Classify the question
            classification = await self.classifier.classify(question)

            # If it's not a data query, return the natural language response
            if not classification.get('is_data_query', True):
                response['success'] = True
                response['explanation'] = classification.get('response', '')

                # Store meta query response in context
                self.context_manager.add_message(
                    session_id=session_id,
                    role='assistant',
                    content=response['explanation'],
                    metadata={'type': 'meta_query'}
                )

                return response

            # Step 3: Generate SQL and execute query
            result = await self.sql_generator.ask(
                question,
                conversation_history=conversation_history
            )

            # Step 4: Extract and validate results
            sql = result.get('sql', '')
            results = result.get('results', [])
            context_used = result.get('context_used', [])

            response['sql'] = sql
            response['results'] = results
            response['confidence'] = self._calculate_confidence(context_used)
            response['explanation'] = result.get('explanation', '')

            # Check if SQL was generated
            if not sql:
                response['warnings'].append("❌ Could not generate SQL for this question.")
                return response

            # Step 5: Validate results
            has_warnings, warning_msg = self.result_validator.validate_results(results, sql)
            if has_warnings:
                response['warnings'].append(warning_msg)

            # Step 6: Generate conversational explanation
            explanation = await self.response_generator.generate(
                question=question,
                sql=sql,
                results=results,
                conversation_history=conversation_history
            )
            response['explanation'] = explanation

            # Step 7: Add suggestions for empty results
            if not results or len(results) == 0:
                response['suggestions'] = self._generate_empty_result_suggestions()

            response['success'] = True

            # Store assistant response in context
            self.context_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=response['explanation'],
                sql=response['sql'],
                results=response['results'],
                metadata={
                    'confidence': response['confidence'],
                    'warnings': response['warnings'],
                    'suggestions': response['suggestions']
                }
            )

        except Exception as e:
            logger.error(f"Pipeline processing error: {e}", exc_info=True)
            response['warnings'].append(f"❌ Error: {str(e)}")

            # Store error response in context
            self.context_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=f"Error: {str(e)}",
                metadata={'error': True}
            )

        return response

    @staticmethod
    def _create_empty_response() -> Dict[str, Any]:
        """
        Create empty response structure.

        Returns:
            Empty response dictionary
        """
        return {
            'success': False,
            'sql': '',
            'results': [],
            'explanation': '',
            'warnings': [],
            'suggestions': [],
            'confidence': 0.0,
            'resolved_question': ''  # Question after reference resolution
        }

    @staticmethod
    def _calculate_confidence(context_used: List) -> float:
        """
        Calculate confidence score based on context usage.

        Args:
            context_used: List of context items used

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # High confidence if context was found and used
        return 0.9 if context_used else 0.5

    @staticmethod
    def _generate_empty_result_suggestions() -> List[str]:
        """
        Generate helpful suggestions for empty results.

        Returns:
            List of suggestion strings
        """
        return [
            "Try rephrasing your question",
            "Check if the column or table name is correct",
            "Ask about what data is available"
        ]
