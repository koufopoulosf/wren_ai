"""
Export Handler

Handles data export in multiple formats:
- CSV export
- JSON export
- Chart generation (auto-detects chart type)
"""

import logging
import json
import io
from typing import List, Dict, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger(__name__)


class ExportHandler:
    """
    Handles exporting query results in various formats.
    
    Supports:
    - CSV export (via pandas)
    - JSON export (pretty-printed)
    - Chart generation (bar, line, pie - auto-detected)
    """
    
    def __init__(
        self, 
        enable_csv: bool = True, 
        enable_json: bool = True, 
        enable_charts: bool = True,
        max_export_rows: int = 10000
    ):
        """
        Initialize export handler.
        
        Args:
            enable_csv: Enable CSV export
            enable_json: Enable JSON export
            enable_charts: Enable chart generation
            max_export_rows: Maximum rows to export
        """
        self.enable_csv = enable_csv
        self.enable_json = enable_json
        self.enable_charts = enable_charts
        self.max_export_rows = max_export_rows
        
        logger.info(
            f"✅ Export handler initialized "
            f"(CSV={enable_csv}, JSON={enable_json}, Charts={enable_charts})"
        )
    
    def to_csv(self, data: List[Dict], filename: str = "query_results.csv") -> Optional[bytes]:
        """
        Convert results to CSV.
        
        Args:
            data: List of result rows
            filename: Filename for download (not used, just for reference)
        
        Returns:
            CSV data as bytes, or None if export disabled/failed
        """
        if not self.enable_csv:
            logger.info("CSV export is disabled")
            return None
        
        if not data:
            logger.warning("No data to export to CSV")
            return None
        
        # Check row limit
        if len(data) > self.max_export_rows:
            logger.warning(
                f"Data exceeds max export rows: {len(data)} > {self.max_export_rows}"
            )
            data = data[:self.max_export_rows]
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Convert to CSV bytes
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode('utf-8')
            
            logger.info(f"✅ Generated CSV: {len(data)} rows, {len(df.columns)} columns")
            return csv_bytes
        
        except Exception as e:
            logger.error(f"❌ Failed to generate CSV: {e}", exc_info=True)
            return None
    
    def to_json(self, data: List[Dict], filename: str = "query_results.json") -> Optional[bytes]:
        """
        Convert results to JSON.
        
        Args:
            data: List of result rows
            filename: Filename for download (not used, just for reference)
        
        Returns:
            JSON data as bytes, or None if export disabled/failed
        """
        if not self.enable_json:
            logger.info("JSON export is disabled")
            return None
        
        if not data:
            logger.warning("No data to export to JSON")
            return None
        
        # Check row limit
        if len(data) > self.max_export_rows:
            logger.warning(
                f"Data exceeds max export rows: {len(data)} > {self.max_export_rows}"
            )
            data = data[:self.max_export_rows]
        
        try:
            # Pretty-print JSON
            json_str = json.dumps(data, indent=2, default=str)
            json_bytes = json_str.encode('utf-8')
            
            logger.info(f"✅ Generated JSON: {len(data)} rows")
            return json_bytes
        
        except Exception as e:
            logger.error(f"❌ Failed to generate JSON: {e}", exc_info=True)
            return None
    
    def can_generate_chart(self, data: List[Dict]) -> bool:
        """
        Determine if data is suitable for chart generation.
        
        Args:
            data: Query results
        
        Returns:
            True if chart can be generated
        """
        if not self.enable_charts or not data:
            return False
        
        # Need at least 2 rows for meaningful chart
        if len(data) < 2:
            return False
        
        # Need at least 2 columns (one for labels, one for values)
        if len(data[0].keys()) < 2:
            return False
        
        # Check if we have numeric data
        first_row = data[0]
        has_numeric = any(
            isinstance(v, (int, float)) 
            for v in first_row.values()
        )
        
        if not has_numeric:
            return False
        
        # Don't chart too many rows (becomes unreadable)
        if len(data) > 50:
            logger.info("Too many rows for chart (>50)")
            return False
        
        return True
    
    def generate_chart(
        self, 
        data: List[Dict],
        chart_type: str = "auto",
        title: str = "Query Results"
    ) -> Optional[bytes]:
        """
        Generate chart from query results.
        
        Args:
            data: Query results
            chart_type: 'auto', 'bar', 'line', 'pie'
            title: Chart title
        
        Returns:
            PNG image bytes, or None if failed
        """
        if not self.can_generate_chart(data):
            logger.info("Data not suitable for chart generation")
            return None
        
        try:
            df = pd.DataFrame(data)
            
            # Auto-detect chart type if needed
            if chart_type == "auto":
                chart_type = self._detect_chart_type(df)
            
            logger.info(f"Generating {chart_type} chart with {len(data)} data points")
            
            # Generate chart based on type
            if chart_type == "bar":
                fig = self._create_bar_chart(df, title)
            elif chart_type == "line":
                fig = self._create_line_chart(df, title)
            elif chart_type == "pie":
                fig = self._create_pie_chart(df, title)
            else:
                fig = self._create_bar_chart(df, title)  # Default to bar
            
            # Convert to PNG
            img_bytes = fig.to_image(format="png", width=800, height=600)
            
            logger.info(f"✅ Generated {chart_type} chart successfully")
            return img_bytes
        
        except Exception as e:
            logger.error(f"❌ Failed to generate chart: {e}", exc_info=True)
            return None
    
    def _detect_chart_type(self, df: pd.DataFrame) -> str:
        """
        Auto-detect appropriate chart type based on data.
        
        Args:
            df: Data frame
        
        Returns:
            Chart type: 'bar', 'line', or 'pie'
        """
        # Check for date/time columns -> line chart
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                return "line"
            
            # Check column name for time-related keywords
            col_lower = str(col).lower()
            if any(term in col_lower for term in ['date', 'time', 'month', 'year', 'day', 'week']):
                # Try to convert to datetime
                try:
                    pd.to_datetime(df[col])
                    return "line"
                except:
                    pass
        
        # If we have few rows and single metric -> pie chart
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(df) <= 10 and len(numeric_cols) == 1:
            return "pie"
        
        # Default to bar chart
        return "bar"
    
    def _create_bar_chart(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create bar chart from dataframe."""
        # Get first text/object column for x-axis, first numeric for y-axis
        text_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(text_cols) > 0 and len(numeric_cols) > 0:
            x_col = text_cols[0]
            y_col = numeric_cols[0]
        elif len(numeric_cols) >= 2:
            # If all numeric, use first two
            x_col = df.columns[0]
            y_col = numeric_cols[0]
        else:
            # Fallback: use first two columns
            x_col = df.columns[0]
            y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        fig = px.bar(
            df,
            x=x_col,
            y=y_col,
            title=title,
            labels={x_col: str(x_col), y_col: str(y_col)}
        )
        
        fig.update_layout(
            showlegend=False,
            template="plotly_white",
            font=dict(size=12)
        )
        
        return fig
    
    def _create_line_chart(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create line chart from dataframe."""
        text_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(text_cols) > 0 and len(numeric_cols) > 0:
            x_col = text_cols[0]
            y_col = numeric_cols[0]
        else:
            x_col = df.columns[0]
            y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        fig = px.line(
            df,
            x=x_col,
            y=y_col,
            title=title,
            markers=True,
            labels={x_col: str(x_col), y_col: str(y_col)}
        )
        
        fig.update_layout(
            template="plotly_white",
            font=dict(size=12)
        )
        
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame, title: str) -> go.Figure:
        """Create pie chart from dataframe."""
        text_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(text_cols) > 0 and len(numeric_cols) > 0:
            labels_col = text_cols[0]
            values_col = numeric_cols[0]
        else:
            labels_col = df.columns[0]
            values_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        fig = px.pie(
            df,
            names=labels_col,
            values=values_col,
            title=title
        )
        
        fig.update_layout(
            template="plotly_white",
            font=dict(size=12)
        )
        
        return fig