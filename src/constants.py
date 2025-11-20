"""
Constants and configuration values for WrenAI.

This module centralizes all magic numbers and configuration constants
to improve maintainability and make the codebase easier to understand.
"""

# ============================================================================
# LLM Configuration
# ============================================================================

# Model names
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Max tokens for different operation types
LLM_MAX_TOKENS_SQL_GENERATION = 2000  # SQL queries can be long
LLM_MAX_TOKENS_SHORT_EXPLANATION = 200  # Brief explanations
LLM_MAX_TOKENS_DETAILED_EXPLANATION = 250  # Contextual explanations
LLM_MAX_TOKENS_CLASSIFICATION = 100  # Question classification
LLM_MAX_TOKENS_CONVERSATIONAL = 300  # Conversational responses

# Temperature settings
LLM_TEMPERATURE_PRECISE = 0.3  # Low temperature for consistent, precise outputs
LLM_TEMPERATURE_CREATIVE = 0.7  # Higher temperature for creative responses
LLM_TEMPERATURE_DEFAULT = 0.5  # Balanced temperature

# ============================================================================
# Database Configuration
# ============================================================================

# Schema caching
SCHEMA_CACHE_TTL_SECONDS = 300  # 5 minutes - balance between freshness and performance

# Query execution
QUERY_EXECUTION_TIMEOUT_SECONDS = 30  # Maximum time for query execution
MAX_QUERY_RESULTS = 1000  # Maximum number of rows to return

# ============================================================================
# Chart Generation
# ============================================================================

# Chart display limits
MAX_CHART_CATEGORIES = 20  # Maximum categories for bar/pie charts
MAX_CHART_DATA_POINTS = 100  # Maximum data points for line charts
DEFAULT_CHART_HEIGHT = 400  # Default chart height in pixels
DEFAULT_CHART_WIDTH = 600  # Default chart width in pixels

# ============================================================================
# UI Configuration
# ============================================================================

# Message display
MAX_MESSAGE_LENGTH = 5000  # Maximum characters in a single message
MESSAGE_TRUNCATION_SUFFIX = "... (truncated)"

# Result display
DEFAULT_RESULTS_PAGE_SIZE = 50  # Default number of results per page
MAX_RESULTS_DISPLAY = 500  # Maximum results to display in UI

# ============================================================================
# Validation
# ============================================================================

# Query validation
MIN_QUERY_LENGTH = 3  # Minimum characters for a valid query
MAX_QUERY_LENGTH = 500  # Maximum characters for a query

# SQL validation
AMBIGUOUS_QUERY_MARKER = "AMBIGUOUS_QUERY"  # Marker for ambiguous queries

# ============================================================================
# Logging
# ============================================================================

# Log message limits
MAX_LOG_LENGTH = 1000  # Maximum length for log messages
