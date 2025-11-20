"""
Custom exception hierarchy for Data Assistant.

This module provides a structured exception hierarchy to enable
better error handling and more precise error catching throughout
the application.
"""


class DataAssistantError(Exception):
    """Base exception for all Data Assistant errors."""
    pass


class LLMError(DataAssistantError):
    """Base exception for LLM-related errors."""
    pass


class LLMAPIError(LLMError):
    """Raised when the LLM API call fails."""
    pass


class LLMResponseError(LLMError):
    """Raised when the LLM response is invalid or unexpected."""
    pass


class DatabaseError(DataAssistantError):
    """Base exception for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class QueryExecutionError(DatabaseError):
    """Raised when query execution fails."""
    pass


class ValidationError(DataAssistantError):
    """Base exception for validation errors."""
    pass


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""
    pass


class QueryValidationError(ValidationError):
    """Raised when query validation fails."""
    pass


class ConfigurationError(DataAssistantError):
    """Raised when configuration is invalid or missing."""
    pass


class ChartGenerationError(DataAssistantError):
    """Raised when chart generation fails."""
    pass
