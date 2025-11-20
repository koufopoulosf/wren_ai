"""
Insight Generator

Extracts key insights and actionable takeaways from query results.

This module analyzes query results to automatically identify:
- Top findings (most important data points)
- Trends and patterns
- Outliers and anomalies
- Actionable recommendations
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from anthropic import Anthropic
import json

from .llm_utils import LLMUtils
from .constants import (
    LLM_MAX_TOKENS_DETAILED_EXPLANATION,
    LLM_TEMPERATURE_PRECISE
)
from .exceptions import LLMError

logger = logging.getLogger(__name__)


@dataclass
class Insights:
    """
    Key insights extracted from query results.

    Attributes:
        top_findings: 3-5 most important findings
        trends: Observable patterns in the data
        outliers: Anomalies or exceptional values
        recommendations: Suggested next steps or actions
        summary: One-line executive summary
    """
    top_findings: List[str]
    trends: List[str]
    outliers: List[str]
    recommendations: List[str]
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'top_findings': self.top_findings,
            'trends': self.trends,
            'outliers': self.outliers,
            'recommendations': self.recommendations,
            'summary': self.summary
        }

    def has_insights(self) -> bool:
        """Check if any insights were found."""
        return bool(
            self.top_findings or
            self.trends or
            self.outliers or
            self.recommendations
        )


class InsightGenerator:
    """
    Extracts key insights and takeaways from query results.

    Analyzes data to find:
    - Top findings (most important)
    - Trends and patterns
    - Outliers and anomalies
    - Actionable insights

    Single Responsibility: Data insight extraction
    """

    def __init__(self, anthropic_client: Anthropic, model: str):
        """
        Initialize insight generator.

        Args:
            anthropic_client: Anthropic API client
            model: Claude model name
        """
        self.client = anthropic_client
        self.model = model
        logger.info("✅ Insight generator initialized")

    async def generate_insights(
        self,
        question: str,
        sql: str,
        results: List[Dict]
    ) -> Insights:
        """
        Generate key takeaways from results.

        Analyzes query results to extract meaningful insights that help
        users understand what the data is telling them.

        Args:
            question: User's original question
            sql: Generated SQL query
            results: Query execution results

        Returns:
            Insights with top findings, trends, outliers, and recommendations
        """
        # Don't generate insights for empty results
        if not results or len(results) == 0:
            return self._create_empty_insights()

        # Don't generate insights for very small result sets (< 3 rows)
        if len(results) < 3:
            return self._create_simple_insights(results)

        try:
            # Build insight generation prompt
            prompt = self._build_insight_prompt(
                question=question,
                sql=sql,
                results=results
            )

            # Get insights from LLM
            response = await LLMUtils.call_claude_async(
                client=self.client,
                model=self.model,
                prompt=prompt,
                max_tokens=LLM_MAX_TOKENS_DETAILED_EXPLANATION,
                temperature=LLM_TEMPERATURE_PRECISE
            )

            # Parse insights
            insights = self._parse_insights_response(response)

            logger.info(
                f"Generated insights - Findings: {len(insights.top_findings)}, "
                f"Trends: {len(insights.trends)}, Outliers: {len(insights.outliers)}"
            )

            return insights

        except (LLMError, json.JSONDecodeError) as e:
            logger.warning(f"Insight generation failed: {e}, returning basic insights")
            return self._create_simple_insights(results)

    def _build_insight_prompt(
        self,
        question: str,
        sql: str,
        results: List[Dict]
    ) -> str:
        """
        Build prompt for insight generation.

        Args:
            question: User's question
            sql: Generated SQL
            results: Query results

        Returns:
            Formatted insight generation prompt
        """
        # Prepare results data
        results_summary = self._format_results_for_analysis(results)

        prompt = f"""You are a data analyst extracting key insights from query results.

**User's Question:**
"{question}"

**SQL Query:**
```sql
{sql}
```

**Query Results:**
{results_summary}

**Your Task:**
Analyze these results and extract actionable insights. Focus on what the data reveals, not just describing it.

Look for:
1. **Top Findings**: Most important/surprising discoveries (3-5 points)
2. **Trends**: Patterns, correlations, or trends in the data
3. **Outliers**: Anomalies, exceptional values, or outliers
4. **Recommendations**: What should the user investigate next or do based on this data?

**Guidelines:**
- Be specific with numbers and percentages
- Compare values when relevant (e.g., "X is 3x larger than Y")
- Identify what's notable or unexpected
- Focus on insights, not obvious observations
- Keep each point concise (1 sentence)

**Respond with JSON only:**
{{
  "summary": "One-line executive summary of key finding",
  "top_findings": ["Finding 1", "Finding 2", "Finding 3"],
  "trends": ["Trend 1", "Trend 2"],
  "outliers": ["Outlier 1"],
  "recommendations": ["Next step 1", "Next step 2"]
}}

**Example for token trading volume query:**
{{
  "summary": "Trading is heavily concentrated in top 3 tokens (78% of total volume)",
  "top_findings": [
    "Bitcoin dominates with $2.3B volume (45% of total)",
    "Top 3 tokens (BTC, ETH, SOL) account for 78% of all trading",
    "Ethereum volume dropped 12% compared to last month"
  ],
  "trends": [
    "Established tokens show increasing volume trend this week",
    "Newer tokens (< 6 months old) have 3x higher volatility"
  ],
  "outliers": [
    "DOGE shows unusual 300% volume spike in last 24 hours"
  ],
  "recommendations": [
    "Investigate why Ethereum volume is declining",
    "Monitor DOGE for potential market event",
    "Consider analyzing volume distribution over time"
  ]
}}

Respond with JSON only, no additional text:"""

        return prompt

    def _format_results_for_analysis(
        self,
        results: List[Dict],
        max_rows: int = 50
    ) -> str:
        """
        Format query results for insight analysis.

        Args:
            results: Query results
            max_rows: Maximum rows to include in analysis

        Returns:
            Formatted results string
        """
        if not results:
            return "No results"

        # Get statistics
        total_rows = len(results)
        columns = list(results[0].keys()) if results else []

        # Build formatted output
        output_lines = [
            f"Total rows: {total_rows}",
            f"Columns: {', '.join(columns)}",
            ""
        ]

        # Add data rows
        rows_to_show = min(len(results), max_rows)
        for i, row in enumerate(results[:rows_to_show]):
            row_str = " | ".join(f"{k}: {v}" for k, v in row.items())
            output_lines.append(f"Row {i+1}: {row_str}")

        if total_rows > rows_to_show:
            output_lines.append(f"... and {total_rows - rows_to_show} more rows")

        # Add summary statistics if numeric columns exist
        stats = self._calculate_basic_stats(results, columns)
        if stats:
            output_lines.append("\nSummary Statistics:")
            output_lines.extend(stats)

        return "\n".join(output_lines)

    def _calculate_basic_stats(
        self,
        results: List[Dict],
        columns: List[str]
    ) -> List[str]:
        """
        Calculate basic statistics for numeric columns.

        Args:
            results: Query results
            columns: Column names

        Returns:
            List of statistic strings
        """
        stats = []

        for col in columns:
            try:
                # Extract numeric values
                values = [
                    float(row[col])
                    for row in results
                    if row[col] is not None and str(row[col]).replace('.', '').replace('-', '').isdigit()
                ]

                if values:
                    min_val = min(values)
                    max_val = max(values)
                    avg_val = sum(values) / len(values)

                    stats.append(
                        f"  {col}: min={min_val:.2f}, max={max_val:.2f}, avg={avg_val:.2f}"
                    )
            except (ValueError, TypeError):
                # Skip non-numeric columns
                continue

        return stats

    def _parse_insights_response(self, response: str) -> Insights:
        """
        Parse insights response from LLM.

        Args:
            response: LLM response (expected to be JSON)

        Returns:
            Parsed Insights

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

        return Insights(
            summary=data.get('summary', ''),
            top_findings=data.get('top_findings', []),
            trends=data.get('trends', []),
            outliers=data.get('outliers', []),
            recommendations=data.get('recommendations', [])
        )

    @staticmethod
    def _create_empty_insights() -> Insights:
        """
        Create empty insights for when there are no results.

        Returns:
            Empty Insights object
        """
        return Insights(
            summary="No results found",
            top_findings=[],
            trends=[],
            outliers=[],
            recommendations=["Try rephrasing your question", "Check if column or table names are correct"]
        )

    @staticmethod
    def _create_simple_insights(results: List[Dict]) -> Insights:
        """
        Create simple insights for small result sets.

        Args:
            results: Query results

        Returns:
            Simple Insights object
        """
        return Insights(
            summary=f"Found {len(results)} result{'s' if len(results) != 1 else ''}",
            top_findings=[f"Query returned {len(results)} row{'s' if len(results) != 1 else ''}"],
            trends=[],
            outliers=[],
            recommendations=[]
        )
