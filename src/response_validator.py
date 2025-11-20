"""
Response Validator

Validates query responses for accuracy and relevance using a second LLM call.

This module performs quality checks on generated responses to ensure:
- SQL correctly addresses the user's question
- Explanation accurately reflects the results
- No logical errors or contradictions
- Appropriate confidence levels
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from anthropic import Anthropic
import json

from .llm_utils import LLMUtils
from .constants import (
    LLM_MAX_TOKENS_CLASSIFICATION,
    LLM_TEMPERATURE_PRECISE
)
from .exceptions import LLMError

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Result of response validation.

    Attributes:
        is_valid: Whether the response passes validation
        confidence: Confidence score (0.0 to 1.0)
        issues: List of problems found
        suggestions: List of improvement suggestions
    """
    is_valid: bool
    confidence: float
    issues: List[str]
    suggestions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'is_valid': self.is_valid,
            'confidence': self.confidence,
            'issues': self.issues,
            'suggestions': self.suggestions
        }


class ResponseValidator:
    """
    Validates responses for accuracy and relevance.

    Performs a second LLM call to check:
    - Does the SQL actually answer the question?
    - Is the explanation accurate given the results?
    - Are there any logical inconsistencies?

    Single Responsibility: Response quality validation
    """

    def __init__(self, anthropic_client: Anthropic, model: str):
        """
        Initialize response validator.

        Args:
            anthropic_client: Anthropic API client
            model: Claude model name
        """
        self.client = anthropic_client
        self.model = model
        logger.info("✅ Response validator initialized")

    async def validate_response(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        explanation: str
    ) -> ValidationResult:
        """
        Validate the complete response.

        Performs comprehensive validation to ensure response quality:
        1. Intent Match: Does SQL answer the question?
        2. Result Consistency: Do results match the explanation?
        3. Logic Errors: Any contradictions?
        4. Completeness: Is the answer complete?
        5. Accuracy: Are numbers/facts correct?

        Args:
            question: User's original question
            sql: Generated SQL query
            results: Query execution results
            explanation: Generated explanation

        Returns:
            ValidationResult with validation details
        """
        try:
            # Build validation prompt
            prompt = self._build_validation_prompt(
                question=question,
                sql=sql,
                results=results,
                explanation=explanation
            )

            # Get validation from LLM
            response = await LLMUtils.call_claude_async(
                client=self.client,
                model=self.model,
                prompt=prompt,
                max_tokens=LLM_MAX_TOKENS_CLASSIFICATION,
                temperature=LLM_TEMPERATURE_PRECISE
            )

            # Parse validation result
            validation = self._parse_validation_response(response)

            logger.info(
                f"Validation complete - Valid: {validation.is_valid}, "
                f"Confidence: {validation.confidence:.2f}"
            )

            return validation

        except (LLMError, json.JSONDecodeError) as e:
            logger.warning(f"Validation failed: {e}, defaulting to medium confidence")

            # Return default medium confidence result on error
            return ValidationResult(
                is_valid=True,
                confidence=0.6,
                issues=[f"Could not perform validation: {str(e)}"],
                suggestions=["Consider rephrasing your question for better results"]
            )

    def _build_validation_prompt(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        explanation: str
    ) -> str:
        """
        Build prompt for validation.

        Args:
            question: User's question
            sql: Generated SQL
            results: Query results
            explanation: Generated explanation

        Returns:
            Formatted validation prompt
        """
        # Summarize results if too many
        results_summary = self._summarize_results(results)

        prompt = f"""You are a quality validator reviewing a Q&A interaction for a database query system.

**User's Question:**
"{question}"

**Generated SQL:**
```sql
{sql}
```

**Query Results Summary:**
{results_summary}

**Explanation Provided to User:**
"{explanation}"

**Your Task:**
Validate this response by checking:

1. **Intent Match**: Does the SQL correctly address what the user asked?
2. **Result Consistency**: Is the explanation accurate given the actual results?
3. **Logic Errors**: Are there any contradictions or logical problems?
4. **Completeness**: Does the response fully answer the question?
5. **Accuracy**: Are any numbers or facts mentioned correct?

**Respond with JSON only:**
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "issues": ["list of specific problems found, or empty list if none"],
  "suggestions": ["list of improvements, or empty list if none"]
}}

**Confidence scoring guide:**
- 0.9-1.0: Excellent match, accurate, complete
- 0.7-0.9: Good match, minor issues
- 0.5-0.7: Acceptable but has problems
- 0.3-0.5: Significant issues
- 0.0-0.3: Poor quality, major problems

Respond with JSON only, no additional text:"""

        return prompt

    def _summarize_results(self, results: List[Dict], max_rows: int = 5) -> str:
        """
        Summarize query results for validation prompt.

        Args:
            results: Query results
            max_rows: Maximum rows to include

        Returns:
            Formatted results summary
        """
        if not results:
            return "No results returned (empty result set)"

        # Get column names from first result
        columns = list(results[0].keys()) if results else []

        # Build summary
        summary_lines = [
            f"Total rows: {len(results)}",
            f"Columns: {', '.join(columns)}"
        ]

        # Add sample rows
        if results:
            summary_lines.append("\nSample rows:")
            for i, row in enumerate(results[:max_rows]):
                row_str = ", ".join(f"{k}={v}" for k, v in row.items())
                summary_lines.append(f"  Row {i+1}: {row_str}")

            if len(results) > max_rows:
                summary_lines.append(f"  ... and {len(results) - max_rows} more rows")

        return "\n".join(summary_lines)

    def _parse_validation_response(self, response: str) -> ValidationResult:
        """
        Parse validation response from LLM.

        Args:
            response: LLM response (expected to be JSON)

        Returns:
            Parsed ValidationResult

        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        # Clean response (remove markdown if present)
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            response = "\n".join(lines)

        # Parse JSON
        data = json.loads(response)

        return ValidationResult(
            is_valid=data.get('is_valid', True),
            confidence=float(data.get('confidence', 0.5)),
            issues=data.get('issues', []),
            suggestions=data.get('suggestions', [])
        )
