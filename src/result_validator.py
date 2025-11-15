"""
Query Result Validator

Validates query results for common issues that might indicate bad queries.
"""

import logging
from typing import List, Dict, Tuple, Any

logger = logging.getLogger(__name__)


class ResultValidator:
    """
    Validates query results for potential issues.

    Checks:
    - Empty results (might be a bad query)
    - Suspicious numeric values (negative revenue, etc.)
    - Excessive row counts (missing LIMIT)
    """

    def __init__(self, max_rows_warning: int = 1000):
        """
        Initialize result validator.

        Args:
            max_rows_warning: Warn if results exceed this many rows
        """
        self.max_rows_warning = max_rows_warning
        logger.info(f"✅ Result validator initialized (max_rows_warning={max_rows_warning})")

    def validate_results(
        self,
        results: List[Dict[str, Any]],
        sql: str
    ) -> Tuple[bool, str]:
        """
        Validate query results.

        Args:
            results: List of result rows
            sql: Original SQL query

        Returns:
            (has_warnings, warning_message)
            - has_warnings: True if issues found
            - warning_message: Description of issues (empty if no issues)
        """
        warnings = []

        # Check 1: Empty results
        if not results or len(results) == 0:
            # Check if query has WHERE clause (might be intentional)
            if 'WHERE' in sql.upper():
                # Has filters, so empty result might be expected
                logger.debug("Empty results but query has WHERE clause - likely intentional")
            else:
                # No filters, empty is suspicious
                warnings.append(
                    "📊 Query returned 0 rows. "
                    "This might indicate a problem with the query."
                )
                logger.warning("⚠️  Empty result set without WHERE clause - suspicious")

        # Check 2: Excessive rows
        elif len(results) >= self.max_rows_warning:
            # Check if query has LIMIT
            if 'LIMIT' not in sql.upper():
                warnings.append(
                    f"⚠️ Query returned {len(results):,} rows without LIMIT. "
                    f"Consider adding LIMIT to improve performance."
                )
                logger.warning(f"⚠️  Large result set ({len(results)} rows) without LIMIT")

        # Check 3: Suspicious numeric values
        if results and len(results) > 0:
            suspicious_values = self._check_suspicious_values(results)
            if suspicious_values:
                warnings.extend(suspicious_values)

        if warnings:
            return True, "\n".join(warnings)

        logger.info(f"✅ Result validation passed ({len(results)} rows)")
        return False, ""

    def _check_suspicious_values(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Check for suspicious numeric values in results.

        Args:
            results: Query results

        Returns:
            List of warning messages
        """
        warnings = []

        # Get column names that might be monetary/count values
        if not results:
            return warnings

        first_row = results[0]
        suspicious_columns = []

        for col_name, value in first_row.items():
            col_lower = col_name.lower()

            # Check if column might be a monetary/count value
            is_monetary = any(word in col_lower for word in [
                'revenue', 'price', 'cost', 'amount', 'total', 'value',
                'sales', 'income', 'profit', 'margin'
            ])

            is_count = any(word in col_lower for word in [
                'count', 'number', 'num', 'quantity', 'qty'
            ])

            if is_monetary or is_count:
                # Check all values in this column
                negative_count = 0
                for row in results:
                    val = row.get(col_name)
                    if isinstance(val, (int, float)) and val < 0:
                        negative_count += 1

                # If many negative values, warn user
                if negative_count > len(results) * 0.5:  # >50% negative
                    suspicious_columns.append(f"`{col_name}` (mostly negative)")
                    logger.warning(f"⚠️  Suspicious values in {col_name}: {negative_count}/{len(results)} negative")

        if suspicious_columns:
            warnings.append(
                f"⚠️ Suspicious values detected in: {', '.join(suspicious_columns)}. "
                "This might indicate an issue with the query logic."
            )

        return warnings

    def get_result_summary(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of query results.

        Args:
            results: Query results

        Returns:
            Human-readable summary
        """
        if not results:
            return "No results returned"

        row_count = len(results)
        col_count = len(results[0]) if results else 0

        summary = f"📊 {row_count:,} row(s), {col_count} column(s)"

        # Add column names
        if results:
            col_names = list(results[0].keys())
            summary += f"\n   Columns: {', '.join(f'`{c}`' for c in col_names)}"

        return summary
