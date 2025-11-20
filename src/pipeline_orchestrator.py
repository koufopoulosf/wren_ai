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
from .exceptions import DataAssistantError

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates the complete query processing pipeline.

    This class coordinates the workflow:
    1. Classify the question
    2. Generate SQL if it's a data query
    3. Execute and validate results
    4. Generate conversational response

    Single Responsibility: Pipeline coordination and workflow management
    """

    def __init__(
        self,
        classifier: QuestionClassifier,
        response_generator: ResponseGenerator,
        sql_generator: SQLGenerator,
        result_validator: ResultValidator
    ):
        """
        Initialize pipeline orchestrator.

        Args:
            classifier: Question classifier instance
            response_generator: Response generator instance
            sql_generator: SQL generator instance
            result_validator: Result validator instance
        """
        self.classifier = classifier
        self.response_generator = response_generator
        self.sql_generator = sql_generator
        self.result_validator = result_validator
        logger.info("✅ Pipeline orchestrator initialized")

    async def process(
        self,
        question: str,
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        Process user question through the complete pipeline.

        Args:
            question: User's natural language question
            conversation_history: List of previous messages for context

        Returns:
            {
                'success': bool,
                'sql': str,
                'results': List[Dict],
                'explanation': str,
                'warnings': List[str],
                'suggestions': List[str],
                'confidence': float
            }
        """
        response = self._create_empty_response()

        try:
            # Step 1: Classify the question
            classification = await self.classifier.classify(question)

            # Step 2: If it's not a data query, return the natural language response
            if not classification.get('is_data_query', True):
                response['success'] = True
                response['explanation'] = classification.get('response', '')
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

        except Exception as e:
            logger.error(f"Pipeline processing error: {e}", exc_info=True)
            response['warnings'].append(f"❌ Error: {str(e)}")

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
            'confidence': 0.0
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
