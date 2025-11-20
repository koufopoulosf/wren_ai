"""
Component Factory

Handles dependency injection and component initialization.
This centralizes the creation of all application components,
making the codebase easier to test and maintain.
"""

import logging
from typing import Optional

from .config import Config
from .sql_generator import SQLGenerator
from .question_classifier import QuestionClassifier
from .response_generator import ResponseGenerator
from .result_validator import ResultValidator
from .query_explainer import QueryExplainer
from .context_manager import ContextManager
from .pipeline_orchestrator import PipelineOrchestrator
from .response_validator import ResponseValidator
from .insight_generator import InsightGenerator
from .confidence_calculator import ConfidenceCalculator

logger = logging.getLogger(__name__)


class ComponentFactory:
    """
    Factory for creating and wiring application components.

    This class encapsulates all dependency wiring logic, making it easy
    to test individual components and maintain the application structure.
    """

    def __init__(self, config: Config):
        """
        Initialize the factory with configuration.

        Args:
            config: Application configuration
        """
        self.config = config
        self._components = {}
        logger.info("ComponentFactory initialized")

    def create_sql_generator(self) -> SQLGenerator:
        """Create and configure SQL generator."""
        if 'sql_generator' not in self._components:
            self._components['sql_generator'] = SQLGenerator(
                anthropic_client=self.config.anthropic_client,
                db_config=self.config.get_db_config(),
                model=self.config.ANTHROPIC_MODEL,
                db_type=self.config.DB_TYPE
            )
            logger.info("✅ SQLGenerator created")
        return self._components['sql_generator']

    def create_question_classifier(self) -> QuestionClassifier:
        """Create and configure question classifier."""
        if 'question_classifier' not in self._components:
            self._components['question_classifier'] = QuestionClassifier(
                anthropic_client=self.config.anthropic_client,
                model=self.config.ANTHROPIC_MODEL
            )
            logger.info("✅ QuestionClassifier created")
        return self._components['question_classifier']

    def create_response_generator(self) -> ResponseGenerator:
        """Create and configure response generator."""
        if 'response_generator' not in self._components:
            self._components['response_generator'] = ResponseGenerator(
                anthropic_client=self.config.anthropic_client,
                model=self.config.ANTHROPIC_MODEL
            )
            logger.info("✅ ResponseGenerator created")
        return self._components['response_generator']

    def create_result_validator(self) -> ResultValidator:
        """Create and configure result validator."""
        if 'result_validator' not in self._components:
            self._components['result_validator'] = ResultValidator()
            logger.info("✅ ResultValidator created")
        return self._components['result_validator']

    def create_query_explainer(self) -> QueryExplainer:
        """Create and configure query explainer."""
        if 'query_explainer' not in self._components:
            self._components['query_explainer'] = QueryExplainer(
                anthropic_client=self.config.anthropic_client,
                model=self.config.ANTHROPIC_MODEL
            )
            logger.info("✅ QueryExplainer created")
        return self._components['query_explainer']

    def create_context_manager(self) -> ContextManager:
        """Create and configure context manager."""
        if 'context_manager' not in self._components:
            self._components['context_manager'] = ContextManager(
                anthropic_client=self.config.anthropic_client,
                model=self.config.ANTHROPIC_MODEL
            )
            logger.info("✅ ContextManager created")
        return self._components['context_manager']

    def create_response_validator(self) -> ResponseValidator:
        """Create and configure response validator."""
        if 'response_validator' not in self._components:
            self._components['response_validator'] = ResponseValidator(
                anthropic_client=self.config.anthropic_client,
                model=self.config.ANTHROPIC_MODEL
            )
            logger.info("✅ ResponseValidator created")
        return self._components['response_validator']

    def create_insight_generator(self) -> InsightGenerator:
        """Create and configure insight generator."""
        if 'insight_generator' not in self._components:
            self._components['insight_generator'] = InsightGenerator(
                anthropic_client=self.config.anthropic_client,
                model=self.config.ANTHROPIC_MODEL
            )
            logger.info("✅ InsightGenerator created")
        return self._components['insight_generator']

    def create_confidence_calculator(self) -> ConfidenceCalculator:
        """Create and configure confidence calculator."""
        if 'confidence_calculator' not in self._components:
            self._components['confidence_calculator'] = ConfidenceCalculator()
            logger.info("✅ ConfidenceCalculator created")
        return self._components['confidence_calculator']

    def create_pipeline_orchestrator(self) -> PipelineOrchestrator:
        """
        Create and configure the complete pipeline orchestrator.

        This method wires together all components needed for the query pipeline.

        Returns:
            Fully configured PipelineOrchestrator
        """
        if 'pipeline_orchestrator' not in self._components:
            self._components['pipeline_orchestrator'] = PipelineOrchestrator(
                classifier=self.create_question_classifier(),
                response_generator=self.create_response_generator(),
                sql_generator=self.create_sql_generator(),
                result_validator=self.create_result_validator(),
                context_manager=self.create_context_manager(),
                response_validator=self.create_response_validator(),
                insight_generator=self.create_insight_generator(),
                confidence_calculator=self.create_confidence_calculator()
            )
            logger.info("✅ PipelineOrchestrator created with all dependencies")
        return self._components['pipeline_orchestrator']

    def get_component(self, component_name: str) -> Optional[object]:
        """
        Get a specific component by name.

        Args:
            component_name: Name of the component to retrieve

        Returns:
            The requested component, or None if not created yet
        """
        return self._components.get(component_name)

    def clear_components(self) -> None:
        """Clear all cached components (useful for testing)."""
        self._components.clear()
        logger.info("All components cleared")
