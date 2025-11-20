"""
Data Assistant

Production-ready Streamlit application for querying databases
using natural language via Claude Sonnet 4.5.
"""

__version__ = "1.0.0"
__author__ = "Your Team"
__description__ = "Natural language data queries via Streamlit"

# Core modules
from .config import Config
from .sql_generator import SQLGenerator
from .query_explainer import QueryExplainer
from .result_validator import ResultValidator
from .question_classifier import QuestionClassifier
from .response_generator import ResponseGenerator
from .pipeline_orchestrator import PipelineOrchestrator
from .context_manager import ContextManager, ConversationContext, Message
from .response_validator import ResponseValidator
from .insight_generator import InsightGenerator
from .confidence_calculator import ConfidenceCalculator

# Utilities
from .llm_utils import LLMUtils
from .constants import *
from .exceptions import *

__all__ = [
    # Core classes
    "Config",
    "SQLGenerator",
    "QueryExplainer",
    "ResultValidator",
    "QuestionClassifier",
    "ResponseGenerator",
    "PipelineOrchestrator",
    "ContextManager",
    "ConversationContext",
    "Message",
    "ResponseValidator",
    "InsightGenerator",
    "ConfidenceCalculator",
    # Utilities
    "LLMUtils",
]