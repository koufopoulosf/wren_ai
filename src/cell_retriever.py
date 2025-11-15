"""
Cell Value Retriever

Retrieves relevant database cell values to help with:
- WHERE clause filters
- Exact value matching
- Avoiding typos in queries

This improves SQL generation accuracy by providing actual database values
that match the user's question.
"""

import logging
from typing import List, Dict, Set, Optional
import asyncio

logger = logging.getLogger(__name__)


class CellRetriever:
    """Retrieve relevant database cell values."""

    def __init__(self, wren_client, max_cells_per_column: int = 10):
        """
        Initialize cell retriever.

        Args:
            wren_client: WrenClient instance for database access
            max_cells_per_column: Maximum distinct values to cache per column
        """
        self.wren = wren_client
        self.max_cells = max_cells_per_column
        self._cell_cache = {}  # {table.column: [values]}
        self._cache_loaded = False

    async def load_cell_cache(self):
        """
        Pre-load cell values for common columns.

        Caches distinct values from:
        - String columns (categorical data)
        - Small-cardinality columns (<100 distinct values)
        """
        if self._cache_loaded:
            return

        logger.info("📦 Loading cell value cache...")

        models = self.wren._mdl_models

        for model in models:
            table_name = model.get('name', '')
            columns = model.get('columns', [])

            # Identify string/categorical columns
            string_columns = [
                col['name'] for col in columns
                if col.get('type', '').lower() in ['string', 'text', 'varchar', 'char']
            ]

            # Sample first few string columns to avoid overload
            for col_name in string_columns[:3]:  # Limit to 3 columns per table
                try:
                    await self._cache_column_values(table_name, col_name)
                except Exception as e:
                    logger.debug(f"Failed to cache {table_name}.{col_name}: {e}")

        self._cache_loaded = True
        logger.info(f"✅ Cell cache loaded: {len(self._cell_cache)} columns cached")

    async def _cache_column_values(self, table: str, column: str):
        """Cache distinct values for a column."""
        key = f"{table}.{column}"

        # Query distinct values
        sql = f"""
            SELECT DISTINCT {column}
            FROM {table}
            WHERE {column} IS NOT NULL
            LIMIT {self.max_cells}
        """

        try:
            results = await self.wren.execute_sql(sql)
            values = [row[column] for row in results if row.get(column)]

            self._cell_cache[key] = values
            logger.debug(f"Cached {len(values)} values for {key}")

        except Exception as e:
            logger.debug(f"Could not cache {key}: {e}")

    async def retrieve_relevant_cells(
        self,
        question: str,
        max_results: int = 5
    ) -> Dict[str, List[str]]:
        """
        Retrieve cell values relevant to question.

        Args:
            question: User's natural language question
            max_results: Maximum values to return per column

        Returns:
            Dictionary mapping "table.column" to list of relevant values
        """
        # Ensure cache is loaded (fixes race condition)
        if not self._cache_loaded:
            logger.info("⏳ Cell cache not loaded yet, loading now...")
            await self.load_cell_cache()

        # Extract keywords from question
        keywords = self._extract_keywords(question)

        if not keywords:
            return {}

        # Find matching cells
        relevant_cells = {}

        for key, values in self._cell_cache.items():
            table, column = key.split('.')

            # Check if any value matches keywords
            matched_values = []

            for value in values:
                value_str = str(value).lower()

                # Exact or substring match
                for keyword in keywords:
                    if keyword in value_str or value_str in keyword:
                        matched_values.append(value)
                        break

                if len(matched_values) >= max_results:
                    break

            if matched_values:
                relevant_cells[key] = matched_values

        return relevant_cells

    def _extract_keywords(self, question: str) -> Set[str]:
        """Extract potential value keywords from question."""
        # Simple extraction - split and filter
        words = question.lower().split()

        # Filter out common words
        stopwords = {
            'what', 'show', 'me', 'the', 'is', 'are', 'was', 'were',
            'from', 'to', 'in', 'on', 'at', 'by', 'for', 'with',
            'total', 'how', 'many', 'much', 'average', 'sum',
            'count', 'list', 'give', 'get', 'find', 'all', 'who',
            'where', 'when', 'which', 'why', 'their', 'them',
            'that', 'this', 'these', 'those', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'can', 'may', 'might', 'must', 'between', 'during',
            'before', 'after', 'above', 'below', 'up', 'down',
            'out', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'all', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 'just', 'a', 'an', 'and', 'or',
            'as', 'if', 'of', 'than'
        }

        keywords = {
            word.strip('.,?!') for word in words
            if len(word) > 2 and word.lower() not in stopwords
        }

        return keywords

    async def get_column_samples(
        self,
        table: str,
        column: str,
        limit: int = 5
    ) -> List[str]:
        """
        Get sample values for a specific column.

        Args:
            table: Table name
            column: Column name
            limit: Number of samples

        Returns:
            List of sample values
        """
        key = f"{table}.{column}"

        # Check cache first
        if key in self._cell_cache:
            return self._cell_cache[key][:limit]

        # Query database
        sql = f"""
            SELECT DISTINCT {column}
            FROM {table}
            WHERE {column} IS NOT NULL
            LIMIT {limit}
        """

        try:
            results = await self.wren.execute_sql(sql)
            values = [row[column] for row in results if row.get(column)]
            return values

        except Exception as e:
            logger.warning(f"Failed to get samples for {key}: {e}")
            return []

    def format_cell_context(self, cells: Dict[str, List[str]]) -> str:
        """Format retrieved cells as context string."""
        if not cells:
            return ""

        lines = ["**Relevant Values Found:**"]

        for key, values in cells.items():
            table, column = key.split('.')
            value_str = ', '.join([f"'{v}'" for v in values[:5]])
            lines.append(f"- `{table}.{column}`: {value_str}")

        return "\n".join(lines)

    def clear_cache(self):
        """Clear the cell cache."""
        self._cell_cache.clear()
        self._cache_loaded = False
        logger.info("🗑️  Cell cache cleared")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        total_values = sum(len(values) for values in self._cell_cache.values())

        return {
            'columns_cached': len(self._cell_cache),
            'total_values': total_values,
            'cache_loaded': self._cache_loaded,
            'avg_values_per_column': total_values / len(self._cell_cache) if self._cell_cache else 0
        }
