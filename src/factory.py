"""
Component Factory (Simplified with Insights)

Handles dependency injection for core components + insights.
"""

import logging
from typing import Optional

from .config import Config
from .sql_generator import SQLGenerator
from .question_classifier import QuestionClassifier
from .response_generator import ResponseGenerator
from .context_manager import ContextManager
from .insight_generator import InsightGenerator
from .pipeline_orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)


class ComponentFactory:
    """
    Simplified factory for core components + insights.

    Creates what's essential:
    - SQL generation
    - Question classification
    - Response generation
    - Context management
    - Insight generation (runs in parallel)
    """

    def __init__(self, config: Config):
        """
        Initialize the factory with configuration.

        Args:
            config: Application configuration
        """
        self.config = config
        self._components = {}
        logger.info("✅ Simplified ComponentFactory initialized")

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

    def create_context_manager(self) -> ContextManager:
        """Create and configure context manager."""
        if 'context_manager' not in self._components:
            self._components['context_manager'] = ContextManager(
                anthropic_client=self.config.anthropic_client,
                model=self.config.ANTHROPIC_MODEL
            )
            logger.info("✅ ContextManager created")
        return self._components['context_manager']

    def create_insight_generator(self) -> InsightGenerator:
        """Create and configure insight generator."""
        if 'insight_generator' not in self._components:
            self._components['insight_generator'] = InsightGenerator(
                anthropic_client=self.config.anthropic_client,
                model=self.config.ANTHROPIC_MODEL
            )
            logger.info("✅ InsightGenerator created")
        return self._components['insight_generator']

    def create_pipeline_orchestrator(self) -> PipelineOrchestrator:
        """
        Create simplified pipeline orchestrator with insights.

        Wires together the essential components:
        - Question classifier
        - Response generator (runs in parallel with insights)
        - SQL generator
        - Context manager
        - Insight generator (runs in parallel with response)

        Returns:
            Simplified PipelineOrchestrator with parallel insights
        """
        if 'pipeline_orchestrator' not in self._components:
            self._components['pipeline_orchestrator'] = PipelineOrchestrator(
                classifier=self.create_question_classifier(),
                response_generator=self.create_response_generator(),
                sql_generator=self.create_sql_generator(),
                context_manager=self.create_context_manager(),
                insight_generator=self.create_insight_generator()
            )
            logger.info("✅ Simplified PipelineOrchestrator created with parallel insights")
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
