"""
Error Handler

Converts technical errors into actionable user guidance.
"""

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Classifies errors and provides actionable guidance.
    """

    def classify_error(self, error: Exception, question: str) -> Tuple[str, str]:
        """
        Classify error and return user-friendly message.

        Args:
            error: The exception that occurred
            question: User's original question

        Returns:
            (error_type, friendly_message)
        """
        error_str = str(error).lower()

        # Timeout errors
        if 'timeout' in error_str or 'timed out' in error_str:
            return self._timeout_error(question)

        # Connection errors
        if 'connection' in error_str or 'refused' in error_str:
            return self._connection_error()

        # Syntax errors
        if 'syntax' in error_str or 'parse' in error_str:
            return self._syntax_error(question)

        # Permission errors
        if 'permission' in error_str or 'denied' in error_str or 'forbidden' in error_str:
            return self._permission_error()

        # Data not found
        if 'not found' in error_str or 'does not exist' in error_str or 'no such' in error_str:
            return self._not_found_error(question)

        # Ambiguous question
        if 'ambiguous' in error_str or 'unclear' in error_str:
            return self._ambiguous_error(question)

        # HTTP errors
        if '404' in error_str:
            return self._not_found_error(question)
        elif '403' in error_str or '401' in error_str:
            return self._permission_error()
        elif '500' in error_str or '502' in error_str or '503' in error_str:
            return self._server_error()

        # Generic error
        return self._generic_error(error_str)

    def _timeout_error(self, question: str) -> Tuple[str, str]:
        """Handle timeout errors."""
        return ("timeout",
            "⏱️ *Query took too long*\n\n"
            "Your query exceeded the 30-second timeout limit.\n\n"
            "*Try:*\n"
            "• Adding a shorter time period (e.g., 'last week' instead of 'all time')\n"
            "• Being more specific about what data you need\n"
            "• Asking for aggregated data instead of all rows\n\n"
            "*Example:*\n"
            "Instead of: `Show all orders`\n"
            "Try: `Total orders last month`"
        )

    def _connection_error(self) -> Tuple[str, str]:
        """Handle connection errors."""
        return ("connection",
            "🔌 *Connection Error*\n\n"
            "I couldn't connect to the data warehouse.\n\n"
            "This is usually temporary. Please:\n"
            "1. Wait a few seconds and try again\n"
            "2. If problem persists, contact your administrator\n\n"
            "Your question has been logged for troubleshooting."
        )

    def _syntax_error(self, question: str) -> Tuple[str, str]:
        """Handle SQL syntax errors."""
        return ("syntax",
            "🤔 *I couldn't understand that question*\n\n"
            "I generated SQL but it has syntax issues.\n\n"
            "*Try:*\n"
            "• Rephrasing your question more simply\n"
            "• Breaking it into smaller questions\n"
            "• Being more specific about what you want\n\n"
            "*Example questions that work well:*\n"
            "• What was revenue last month?\n"
            "• Show top 10 customers by order count\n"
            "• How many active users do we have?"
        )

    def _permission_error(self) -> Tuple[str, str]:
        """Handle permission errors."""
        return ("permission",
            "🔒 *Access Denied*\n\n"
            "You don't have permission to access this data.\n\n"
            "Please contact your administrator for access."
        )

    def _not_found_error(self, question: str) -> Tuple[str, str]:
        """Handle data not found errors."""
        # Extract what wasn't found
        entities = self._extract_entities(question)

        msg = "😕 *Data Not Found*\n\n"

        if entities:
            msg += f"I couldn't find data about: {', '.join(entities)}\n\n"

        msg += (
            "*Try:*\n"
            "• Checking the spelling\n"
            "• Using a different term (e.g., 'customers' instead of 'clients')\n"
            "• Asking what data is available: `What tables can I query?`"
        )

        return ("not_found", msg)

    def _ambiguous_error(self, question: str) -> Tuple[str, str]:
        """Handle ambiguous questions."""
        # Detect what's ambiguous
        missing = []

        if not self._has_time_period(question):
            missing.append("time period (e.g., 'last month', 'this year')")

        if not self._has_metric(question):
            missing.append("specific metric (e.g., 'revenue', 'orders', 'users')")

        msg = "🤔 *Your question is a bit unclear*\n\n"

        if missing:
            msg += "I need more information about:\n"
            for item in missing:
                msg += f"• {item}\n"
            msg += "\n"

        msg += (
            "*Try being more specific:*\n"
            "Instead of: `Show performance`\n"
            "Try: `Show revenue by region last quarter`"
        )

        return ("ambiguous", msg)

    def _server_error(self) -> Tuple[str, str]:
        """Handle server errors."""
        return ("server_error",
            "🔧 *Server Error*\n\n"
            "The data warehouse is experiencing issues.\n\n"
            "Please:\n"
            "1. Try again in a few moments\n"
            "2. If this continues, contact your administrator\n\n"
            "The error has been logged for investigation."
        )

    def _generic_error(self, error_str: str) -> Tuple[str, str]:
        """Handle generic errors."""
        # Sanitize error for display (truncate and remove sensitive info)
        safe_error = error_str[:200]

        # Remove potential sensitive patterns
        safe_error = re.sub(r'password[=:]\S+', 'password=***', safe_error, flags=re.IGNORECASE)
        safe_error = re.sub(r'key[=:]\S+', 'key=***', safe_error, flags=re.IGNORECASE)
        safe_error = re.sub(r'token[=:]\S+', 'token=***', safe_error, flags=re.IGNORECASE)

        return ("generic",
            f"❌ *Something went wrong*\n\n"
            f"Error: {safe_error}\n\n"
            "*Try:*\n"
            "• Rephrasing your question\n"
            "• Asking something simpler\n"
            "• Contacting your administrator if this keeps happening"
        )

    def _extract_entities(self, question: str) -> list:
        """Extract potential entity names from question."""
        # Simple extraction - look for capitalized words and common terms
        words = question.split()
        entities = []

        for word in words:
            # Remove punctuation
            clean = word.strip('?!.,;:')

            # Capitalized words (but not first word)
            if clean and clean[0].isupper() and word != words[0]:
                entities.append(clean)

        return entities[:3]  # Limit to 3 entities

    def _has_time_period(self, question: str) -> bool:
        """Check if question has time period."""
        time_words = [
            'today', 'yesterday', 'week', 'month', 'quarter', 'year',
            'last', 'this', 'current', 'recent', '2024', '2023', '2025',
            'daily', 'weekly', 'monthly', 'quarterly', 'yearly',
            'day', 'days', 'ago'
        ]
        question_lower = question.lower()
        return any(word in question_lower for word in time_words)

    def _has_metric(self, question: str) -> bool:
        """Check if question has specific metric."""
        metrics = [
            'revenue', 'sales', 'orders', 'customers', 'users',
            'profit', 'cost', 'margin', 'conversion', 'retention',
            'count', 'total', 'sum', 'average', 'max', 'min',
            'growth', 'rate', 'percentage', 'number'
        ]
        question_lower = question.lower()
        return any(metric in question_lower for metric in metrics)
