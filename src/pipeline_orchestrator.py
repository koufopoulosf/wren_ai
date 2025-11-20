"""
Pipeline Orchestrator

Orchestrates the query processing pipeline from question to results.
"""

import logging
import asyncio
from typing import Dict, Any, List
from anthropic import Anthropic

from .question_classifier import QuestionClassifier
from .response_generator import ResponseGenerator
from .sql_generator import SQLGenerator
from .result_validator import ResultValidator
from .context_manager import ContextManager
from .response_validator import ResponseValidator
from .insight_generator import InsightGenerator
from .confidence_calculator import ConfidenceCalculator
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
        context_manager: ContextManager,
        response_validator: ResponseValidator,
        insight_generator: InsightGenerator,
        confidence_calculator: ConfidenceCalculator
    ):
        """
        Initialize pipeline orchestrator.

        Args:
            classifier: Question classifier instance
            response_generator: Response generator instance
            sql_generator: SQL generator instance
            result_validator: Result validator instance
            context_manager: Context manager for conversation memory
            response_validator: Response validator for quality checks
            insight_generator: Insight generator for key findings
            confidence_calculator: Confidence calculator for scoring
        """
        self.classifier = classifier
        self.response_generator = response_generator
        self.sql_generator = sql_generator
        self.result_validator = result_validator
        self.context_manager = context_manager
        self.response_validator = response_validator
        self.insight_generator = insight_generator
        self.confidence_calculator = confidence_calculator
        logger.info("✅ Pipeline orchestrator initialized with all Phase 2 components")

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
                'resolved_question': str,  # Question after reference resolution
                'validation': ValidationResult,  # Response validation details
                'insights': Insights,  # Key findings and takeaways
                'confidence_details': ConfidenceScore  # Detailed confidence breakdown
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

            # Step 6 & 8: Parallelize independent LLM calls for better performance
            # Run response generation and insights generation in parallel
            explanation_task = self.response_generator.generate(
                question=question,
                sql=sql,
                results=results,
                conversation_history=conversation_history
            )

            # Only generate insights if we have results
            if results and len(results) > 0:
                insights_task = self.insight_generator.generate_insights(
                    question=question,
                    sql=sql,
                    results=results
                )
                # Execute both tasks in parallel
                explanation, insights = await asyncio.gather(
                    explanation_task,
                    insights_task
                )
                response['insights'] = insights.to_dict()

                # Add insight summary to suggestions if available
                if insights.has_insights() and insights.summary:
                    response['suggestions'].insert(0, f"💡 {insights.summary}")
            else:
                # Only explanation needed, no insights
                explanation = await explanation_task

            response['explanation'] = explanation

            # Step 7: Validate response quality (Phase 2)
            validation = await self.response_validator.validate_response(
                question=question,
                sql=sql,
                results=results,
                explanation=explanation
            )
            response['validation'] = validation.to_dict()

            # Add validation warnings if confidence is low
            if validation.confidence < 0.7:
                response['warnings'].append(
                    f"⚠️ {validation.message if hasattr(validation, 'message') else 'Moderate confidence in this answer'}"
                )

            # Add validation issues as warnings
            if validation.issues:
                for issue in validation.issues:
                    response['warnings'].append(f"⚠️ {issue}")

            # Step 9: Calculate detailed confidence score (Phase 2)
            confidence_score = self.confidence_calculator.calculate_confidence(
                question=question,
                sql=sql,
                results=results,
                validation_score=validation.confidence,
                context_used=context_used,
                schema_info=None  # Could pass schema info in future
            )
            response['confidence'] = confidence_score.overall
            response['confidence_details'] = confidence_score.to_dict()

            # Update warnings based on confidence level
            if confidence_score.level == 'low':
                if confidence_score.message not in str(response['warnings']):
                    response['warnings'].append(confidence_score.message)

            # Step 10: Add suggestions for empty results
            if not results or len(results) == 0:
                response['suggestions'].extend(self._generate_empty_result_suggestions())

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
                    'confidence_details': response['confidence_details'],
                    'validation': response['validation'],
                    'insights': response['insights'],
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
            'resolved_question': '',  # Question after reference resolution
            'validation': None,  # Will be populated by ResponseValidator
            'insights': None,  # Will be populated by InsightGenerator
            'confidence_details': None  # Will be populated by ConfidenceCalculator
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
