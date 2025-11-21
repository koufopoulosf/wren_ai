"""
Component Factory (Simplified)

Handles dependency injection for core components.
"""

import logging
from typing import Optional, Type, TypeVar, Any

from config import Config
from sql_generator import SQLGenerator
from question_classifier import QuestionClassifier
from response_generator import ResponseGenerator
from context_manager import ContextManager
from pipeline_orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Generic type for component creation


class ComponentFactory:
    """
    Simplified factory for core components.

    Creates what's essential:
    - SQL generation
    - Question classification
    - Response generation (includes on-demand insights)
    - Context management
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

    def _create_component(
        self,
        component_name: str,
        component_class: Type[T],
        **kwargs: Any
    ) -> T:
        """
        Generic component creation with caching.

        Args:
            component_name: Name for caching
            component_class: Class to instantiate
            **kwargs: Constructor arguments

        Returns:
            Component instance (cached)
        """
        if component_name not in self._components:
            self._components[component_name] = component_class(**kwargs)
            logger.info(f"✅ {component_class.__name__} created")
        return self._components[component_name]

    def create_sql_generator(self) -> SQLGenerator:
        """Create and configure SQL generator."""
        return self._create_component(
            'sql_generator',
            SQLGenerator,
            anthropic_client=self.config.anthropic_client,
            db_config=self.config.get_db_config(),
            model=self.config.ANTHROPIC_MODEL,
            db_type=self.config.DB_TYPE
        )

    def create_question_classifier(self) -> QuestionClassifier:
        """Create and configure question classifier."""
        return self._create_component(
            'question_classifier',
            QuestionClassifier,
            anthropic_client=self.config.anthropic_client,
            model=self.config.ANTHROPIC_MODEL
        )

    def create_response_generator(self) -> ResponseGenerator:
        """Create and configure response generator."""
        return self._create_component(
            'response_generator',
            ResponseGenerator,
            anthropic_client=self.config.anthropic_client,
            model=self.config.ANTHROPIC_MODEL
        )

    def create_context_manager(self) -> ContextManager:
        """Create and configure context manager."""
        return self._create_component(
            'context_manager',
            ContextManager,
            anthropic_client=self.config.anthropic_client,
            model=self.config.ANTHROPIC_MODEL
        )

    def create_pipeline_orchestrator(self) -> PipelineOrchestrator:
        """
        Create simplified pipeline orchestrator.

        Wires together the essential components:
        - Question classifier
        - Response generator (includes on-demand insights generation)
        - SQL generator
        - Context manager

        Returns:
            Simplified PipelineOrchestrator
        """
        if 'pipeline_orchestrator' not in self._components:
            self._components['pipeline_orchestrator'] = PipelineOrchestrator(
                classifier=self.create_question_classifier(),
                response_generator=self.create_response_generator(),
                sql_generator=self.create_sql_generator(),
                context_manager=self.create_context_manager()
            )
            logger.info("✅ Simplified PipelineOrchestrator created")
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
