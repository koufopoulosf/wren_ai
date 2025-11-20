"""
Confidence Calculator

Calculates confidence scores for query responses based on multiple factors.

This module evaluates response quality and provides confidence metrics:
- Schema match quality
- Result quality and completeness
- Validation scores
- Context usage effectiveness
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceScore:
    """
    Confidence score with breakdown by factor.

    Attributes:
        overall: Overall confidence (0.0 to 1.0)
        schema_match: How well SQL matched schema (0.0 to 1.0)
        result_quality: Quality of results returned (0.0 to 1.0)
        validation_score: Validation check score (0.0 to 1.0)
        context_usage: How well context was used (0.0 to 1.0)
        factors: Detailed breakdown of factors
        level: Confidence level (high/medium/low)
        message: User-facing confidence message
    """
    overall: float
    schema_match: float
    result_quality: float
    validation_score: float
    context_usage: float
    factors: Dict[str, Any]
    level: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'overall': self.overall,
            'schema_match': self.schema_match,
            'result_quality': self.result_quality,
            'validation_score': self.validation_score,
            'context_usage': self.context_usage,
            'factors': self.factors,
            'level': self.level,
            'message': self.message
        }


class ConfidenceCalculator:
    """
    Calculate confidence score for responses.

    Evaluates multiple factors:
    - Schema match quality (0-1)
    - Result quality and count (0-1)
    - Validation score (0-1)
    - Context usage effectiveness (0-1)
    - Historical success indicators

    Single Responsibility: Confidence scoring
    """

    # Confidence level thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    MEDIUM_CONFIDENCE_THRESHOLD = 0.5

    # Factor weights (must sum to 1.0)
    WEIGHTS = {
        'schema_match': 0.2,
        'result_quality': 0.3,
        'validation_score': 0.3,
        'context_usage': 0.2
    }

    def __init__(self):
        """Initialize confidence calculator."""
        logger.info("✅ Confidence calculator initialized")

    def calculate_confidence(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        validation_score: Optional[float] = None,
        context_used: Optional[List] = None,
        schema_info: Optional[Dict] = None
    ) -> ConfidenceScore:
        """
        Calculate overall confidence based on multiple factors.

        Args:
            question: User's question
            sql: Generated SQL query
            results: Query execution results
            validation_score: Score from ResponseValidator (0-1)
            context_used: List of context items used
            schema_info: Schema information used

        Returns:
            ConfidenceScore with overall score and breakdown
        """
        # Calculate individual factor scores
        schema_match = self._calculate_schema_match(sql, schema_info)
        result_quality = self._calculate_result_quality(results, question)
        validation = validation_score if validation_score is not None else 0.6
        context = self._calculate_context_usage(context_used)

        # Calculate weighted overall score
        overall = (
            self.WEIGHTS['schema_match'] * schema_match +
            self.WEIGHTS['result_quality'] * result_quality +
            self.WEIGHTS['validation_score'] * validation +
            self.WEIGHTS['context_usage'] * context
        )

        # Determine confidence level and message
        level, message = self._determine_confidence_level(overall)

        # Build detailed factors
        factors = {
            'schema_match_details': self._explain_schema_match(schema_match),
            'result_quality_details': self._explain_result_quality(result_quality, results),
            'validation_details': self._explain_validation(validation),
            'context_details': self._explain_context_usage(context, context_used)
        }

        logger.info(
            f"Confidence calculated - Overall: {overall:.2f}, "
            f"Schema: {schema_match:.2f}, Results: {result_quality:.2f}, "
            f"Validation: {validation:.2f}, Context: {context:.2f}"
        )

        return ConfidenceScore(
            overall=overall,
            schema_match=schema_match,
            result_quality=result_quality,
            validation_score=validation,
            context_usage=context,
            factors=factors,
            level=level,
            message=message
        )

    def _calculate_schema_match(
        self,
        sql: str,
        schema_info: Optional[Dict]
    ) -> float:
        """
        Calculate schema match quality.

        Args:
            sql: Generated SQL
            schema_info: Schema information

        Returns:
            Schema match score (0.0 to 1.0)
        """
        if not sql:
            return 0.0

        score = 0.5  # Base score for having SQL

        # Increase score if SQL is non-trivial (has WHERE, JOIN, etc.)
        sql_upper = sql.upper()
        if 'WHERE' in sql_upper:
            score += 0.15
        if 'JOIN' in sql_upper:
            score += 0.15
        if 'GROUP BY' in sql_upper or 'ORDER BY' in sql_upper:
            score += 0.1
        if 'LIMIT' in sql_upper:
            score += 0.1

        return min(score, 1.0)

    def _calculate_result_quality(
        self,
        results: List[Dict],
        question: str
    ) -> float:
        """
        Calculate result quality score.

        Args:
            results: Query results
            question: User's question

        Returns:
            Result quality score (0.0 to 1.0)
        """
        if not results:
            # Empty results might be valid (e.g., "are there any...?")
            question_lower = question.lower()
            if any(word in question_lower for word in ['any', 'exists', 'is there', 'are there']):
                return 0.7  # Empty result is actually a valid answer
            return 0.3  # Empty result is concerning

        # Score based on result count
        result_count = len(results)

        if result_count == 1:
            score = 0.7  # Single result is good for specific queries
        elif 2 <= result_count <= 10:
            score = 0.9  # Ideal range for most queries
        elif 11 <= result_count <= 100:
            score = 0.8  # Good amount of data
        elif 101 <= result_count <= 1000:
            score = 0.7  # Large result set
        else:
            score = 0.6  # Very large result set might need limiting

        # Increase score if results have multiple columns (richer data)
        if results and len(results[0].keys()) >= 3:
            score += 0.1

        return min(score, 1.0)

    def _calculate_context_usage(self, context_used: Optional[List]) -> float:
        """
        Calculate context usage effectiveness.

        Args:
            context_used: List of context items used

        Returns:
            Context usage score (0.0 to 1.0)
        """
        if context_used is None:
            return 0.5  # Neutral if no context tracking

        if not context_used:
            return 0.5  # No context used (might be first query)

        # Score based on how much context was used
        context_count = len(context_used)

        if context_count == 1:
            return 0.7
        elif context_count == 2:
            return 0.85
        elif context_count >= 3:
            return 0.95

        return 0.5

    def _determine_confidence_level(self, overall: float) -> tuple[str, str]:
        """
        Determine confidence level and user message.

        Args:
            overall: Overall confidence score

        Returns:
            Tuple of (level, message)
        """
        if overall >= self.HIGH_CONFIDENCE_THRESHOLD:
            return (
                "high",
                "🟢 High confidence in this response"
            )
        elif overall >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return (
                "medium",
                "🟡 Moderate confidence - please verify important details"
            )
        else:
            return (
                "low",
                "🔴 Low confidence - please verify this response carefully"
            )

    def _explain_schema_match(self, score: float) -> str:
        """Explain schema match score."""
        if score >= 0.8:
            return "SQL query uses appropriate schema elements and complexity"
        elif score >= 0.5:
            return "SQL query is functional but may be simplified"
        else:
            return "SQL query may not fully utilize schema or is too basic"

    def _explain_result_quality(self, score: float, results: List[Dict]) -> str:
        """Explain result quality score."""
        count = len(results) if results else 0

        if score >= 0.8:
            return f"Results look good ({count} rows with rich data)"
        elif score >= 0.5:
            if count == 0:
                return "No results found - may be expected or query needs refinement"
            else:
                return f"Results returned ({count} rows) but may need review"
        else:
            return "Result quality is concerning - please verify"

    def _explain_validation(self, score: float) -> str:
        """Explain validation score."""
        if score >= 0.8:
            return "Response passed validation checks with high confidence"
        elif score >= 0.5:
            return "Response passed validation with moderate confidence"
        else:
            return "Response has validation concerns"

    def _explain_context_usage(
        self,
        score: float,
        context_used: Optional[List]
    ) -> str:
        """Explain context usage score."""
        if context_used is None:
            return "Context tracking not available"

        count = len(context_used) if context_used else 0

        if count == 0:
            return "No conversation context used (possibly first query)"
        elif count == 1:
            return "Used 1 context item from conversation"
        else:
            return f"Used {count} context items from conversation"
