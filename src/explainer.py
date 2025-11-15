"""
Query Explainer

Converts SQL queries to plain English using Claude Sonnet 4.5.
"""

import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class QueryExplainer:
    """
    Explains SQL queries in plain English using Claude.
    
    Generates concise 1-2 sentence explanations that help users
    understand what the query will do before execution.
    """
    
    def __init__(self, anthropic_client: Anthropic, model: str):
        """
        Initialize explainer with Anthropic client.
        
        Args:
            anthropic_client: Anthropic API client
            model: Claude model name (e.g., 'claude-sonnet-4-20250514')
        """
        self.client = anthropic_client
        self.model = model
        logger.info(f"✅ Query explainer initialized with {model}")
    
    async def explain(self, sql: str) -> str:
        """
        Generate plain English explanation of SQL.
        
        Args:
            sql: SQL query to explain
        
        Returns:
            1-2 sentence explanation
        
        Example:
            >>> explainer = QueryExplainer(client, model)
            >>> sql = '''
            ... SELECT SUM(amount) as revenue
            ... FROM orders
            ... WHERE date >= '2024-10-01'
            ...   AND status = 'completed'
            ... '''
            >>> explanation = await explainer.explain(sql)
            >>> print(explanation)
            "This query calculates total revenue from completed orders
             placed since October 1st, 2024."
        """
        prompt = f"""Explain this SQL query in 1-2 simple, clear sentences.
Focus on: what data is being retrieved, how it's filtered, and what calculations are performed.

Use plain English that non-technical users can understand.

SQL:
```sql
{sql}
```

Provide only the explanation, no other text or formatting."""

        try:
            logger.info("Generating SQL explanation with Claude")
            
            # Call Claude API (synchronous)
            message = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.3,  # Low temperature for consistent explanations
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract explanation text
            explanation = message.content[0].text.strip()
            
            # Remove any markdown formatting
            explanation = explanation.replace('**', '')
            explanation = explanation.replace('*', '')
            
            logger.info(f"✅ Generated explanation ({len(explanation)} chars)")
            logger.debug(f"Explanation: {explanation}")
            
            return explanation
        
        except Exception as e:
            logger.error(f"❌ Failed to generate explanation: {e}", exc_info=True)
            
            # Fallback to basic explanation
            return self._basic_explanation(sql)
    
    def _basic_explanation(self, sql: str) -> str:
        """
        Generate basic explanation without Claude (fallback).
        
        Args:
            sql: SQL query
        
        Returns:
            Simple explanation based on SQL keywords
        """
        sql_upper = sql.upper()
        
        # Detect aggregations
        if any(agg in sql_upper for agg in ['SUM(', 'COUNT(', 'AVG(', 'MAX(', 'MIN(']):
            if 'SUM(' in sql_upper:
                return "This query calculates a total sum from your data."
            elif 'COUNT(' in sql_upper:
                return "This query counts the number of records matching your criteria."
            elif 'AVG(' in sql_upper:
                return "This query calculates an average value from your data."
            elif 'MAX(' in sql_upper or 'MIN(' in sql_upper:
                return "This query finds the maximum or minimum value in your data."
        
        # Detect GROUP BY
        if 'GROUP BY' in sql_upper:
            return "This query groups and summarizes your data by specific categories."
        
        # Detect ORDER BY with LIMIT
        if 'ORDER BY' in sql_upper and 'LIMIT' in sql_upper:
            return "This query retrieves the top results from your data, sorted by a specific criteria."
        
        # Generic explanation
        return "This query retrieves data from your warehouse based on specific filters."