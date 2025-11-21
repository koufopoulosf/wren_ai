"""
Crypto Data Assistant - Streamlit Interface

Modern chat interface for querying cryptocurrency data with natural language.
Features:
- Claude-like clean aesthetics
- Progressive clarification
- Multi-format exports (CSV, JSON, charts)
- Real-time query validation
- Entity discovery and suggestions
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import logging
from typing import Dict, List, Any
import sys
import os

# Set up logger for this module
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from factory import ComponentFactory

# Page config
st.set_page_config(
    page_title="Crypto Data Assistant",
    page_icon="₿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Claude-like aesthetics
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Hide sidebar completely */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* Hide sidebar collapse button */
    button[kind="header"] {
        display: none;
    }

    /* Keep header visible but minimal */
    header[data-testid="stHeader"] {
        background-color: transparent;
    }

    /* Main container - centered like Claude */
    .main {
        background-color: #ffffff;
        max-width: 900px;
        margin: 0 auto;
        padding: 1rem 2rem;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 900px;
    }

    /* Chat message styling - Claude-like */
    .user-message {
        background-color: #f7f7f8;
        padding: 20px 24px;
        border-radius: 12px;
        margin: 12px 0;
        font-size: 15px;
        line-height: 1.65;
        color: #1f2937;
        font-weight: 400;
    }

    .assistant-message {
        background-color: #ffffff;
        padding: 20px 24px;
        border-radius: 12px;
        margin: 12px 0;
        font-size: 15px;
        line-height: 1.65;
        color: #1f2937;
    }

    /* Code blocks - like Claude */
    .stCodeBlock {
        background-color: #f6f8fa;
        border-radius: 8px;
        border: 1px solid #d0d7de;
    }

    /* Buttons - minimal and clean */
    .stButton>button {
        border-radius: 6px;
        border: 1px solid #e5e7eb;
        padding: 8px 16px;
        background-color: #ffffff;
        color: #1f2937;
        font-weight: 500;
        font-size: 14px;
    }

    .stButton>button:hover {
        background-color: #f7f7f8;
        border-color: #d1d5db;
    }

    .stButton>button[kind="primary"] {
        background-color: #1f2937;
        color: white;
        border: none;
    }

    .stButton>button[kind="primary"]:hover {
        background-color: #111827;
    }

    /* Chat input - clean and modern */
    .stChatInput {
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        padding: 12px 16px;
        font-size: 15px;
    }

    .stChatInput:focus {
        border-color: #9ca3af;
        box-shadow: 0 0 0 3px rgba(156, 163, 175, 0.1);
    }

    /* Expander - clean */
    .streamlit-expanderHeader {
        background-color: #f6f8fa;
        border-radius: 6px;
        font-weight: 500;
    }

    /* Success/Info/Warning/Error - subtle */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
        padding: 12px 16px;
    }

    /* Remove extra padding */
    .element-container {
        margin: 0;
    }

    /* Title styling */
    h1 {
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.5rem;
        font-size: 28px;
    }

    h2, h3 {
        font-weight: 600;
        color: #374151;
    }

    /* Dataframe styling */
    .dataframe {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        font-size: 14px;
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 500;
        background-color: #d1fae5;
        color: #065f46;
        margin-bottom: 1rem;
    }

    /* Welcome message */
    .welcome-message {
        text-align: center;
        padding: 3rem 2rem;
        color: #6b7280;
    }

    .welcome-message h2 {
        color: #1f2937;
        margin-bottom: 1rem;
    }

    /* Example queries */
    .example-query {
        background-color: #f7f7f8;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        cursor: pointer;
        font-size: 14px;
    }

    .example-query:hover {
        background-color: #ffffff;
        border-color: #9ca3af;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


class DataAssistant:
    """
    Main application class - Simplified UI coordinator.

    This class is now focused solely on UI coordination and initialization.
    The heavy lifting is done by specialized components:
    - QuestionClassifier: Classifies question intent
    - ResponseGenerator: Generates conversational responses
    - PipelineOrchestrator: Coordinates the workflow
    """

    def __init__(self):
        """Initialize data assistant with factory pattern."""
        self.config = Config()
        self.factory = ComponentFactory(self.config)
        self.initialized = False
        self.schema_info = {"tables": [], "relationships": []}

    async def initialize(self):
        """Initialize async components using factory pattern."""
        if self.initialized:
            return

        # Create orchestrator (factory handles all component wiring)
        self.orchestrator = self.factory.create_pipeline_orchestrator()

        # Get SQL generator for schema loading
        sql_generator = self.factory.get_component('sql_generator')

        # Load basic schema info for display
        await sql_generator.connect_db()
        try:
            # Get table names using public method
            table_names = await sql_generator.get_table_names()
            self.schema_info["tables"] = [{"name": name} for name in table_names]
            logger.info(f"✅ Loaded schema: {len(self.schema_info['tables'])} tables")
        except Exception as e:
            logger.warning(f"Could not load schema info: {e}")
            self.schema_info["tables"] = []

        self.initialized = True
        logger.info("✅ DataAssistant fully initialized with all components")

    async def process_question(
        self,
        question: str,
        session_id: str = "default",
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        Process user question through the pipeline orchestrator with context management.

        This method now delegates to the PipelineOrchestrator for all
        question processing logic, keeping DataAssistant focused on
        UI coordination.

        Args:
            question: User's natural language question
            session_id: Session identifier for context management
            conversation_history: List of previous messages for context (deprecated - use context manager)

        Returns:
            {
                'success': bool,
                'sql': str,
                'results': List[Dict],
                'explanation': str,
                'warnings': List[str],
                'suggestions': List[str],
                'confidence': float,
                'resolved_question': str  # Question after reference resolution
            }
        """
        # Delegate to orchestrator with session_id for context management
        return await self.orchestrator.process(
            question=question,
            session_id=session_id,
            conversation_history=conversation_history
        )


def init_session_state() -> None:
    """Initialize session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'assistant' not in st.session_state:
        st.session_state.assistant = DataAssistant()

    if 'initialized' not in st.session_state:
        st.session_state.initialized = False


def display_message(role: str, content: str, metadata: Dict[str, Any] = None) -> None:
    """Display a chat message with styling."""
    if role == "user":
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)

        # Display metadata if present
        if metadata:
            if metadata.get('sql'):
                with st.expander("💻 View SQL Query", expanded=False):
                    st.code(metadata['sql'], language='sql')

            if metadata.get('results'):
                results = metadata['results']
                df = pd.DataFrame(results)

                with st.expander(f"📊 Results ({len(results)} rows)", expanded=True):
                    st.dataframe(df, use_container_width=True, height=min(400, len(results) * 35 + 38))

                    # Action buttons row 1: Export options
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        # CSV export
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "⬇ CSV",
                            csv,
                            f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv",
                            key=f"csv_{metadata.get('timestamp', '')}",
                            use_container_width=True
                        )

                    with col2:
                        # Excel export
                        from io import BytesIO
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='Query Results')
                            # Auto-adjust column widths
                            worksheet = writer.sheets['Query Results']
                            for idx, col in enumerate(df.columns):
                                max_length = max(
                                    df[col].astype(str).apply(len).max(),
                                    len(str(col))
                                )
                                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)

                        st.download_button(
                            "⬇ Excel",
                            buffer.getvalue(),
                            f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"excel_{metadata.get('timestamp', '')}",
                            use_container_width=True
                        )

                    with col3:
                        # Chart button
                        if st.button("📈 Chart", key=f"chart_{metadata.get('timestamp', '')}", use_container_width=True):
                            st.session_state[f'show_chart_{metadata.get("timestamp", "")}'] = True

                    # Action buttons row 2: Insights button (only if insights not already shown)
                    if not metadata.get('insights'):
                        st.markdown("")  # Spacing
                        if st.button("💎 Show Key Takeaways & Recommendations", key=f"insights_btn_{metadata.get('timestamp', '')}", use_container_width=True):
                            st.session_state[f'request_insights_{metadata.get("timestamp", "")}'] = True
                            st.rerun()

                # Show chart if requested
                if st.session_state.get(f'show_chart_{metadata.get("timestamp", "")}'):
                    create_chart(df, unique_id=metadata.get("timestamp", ""))

            # Display Phase 2 features: Insights
            insights = metadata.get('insights')
            if insights and isinstance(insights, dict):
                # Check if there are any insights to show
                has_content = any([
                    insights.get('top_findings'),
                    insights.get('trends'),
                    insights.get('outliers'),
                    insights.get('recommendations')
                ])

                if has_content:
                    with st.expander("💎 Key Insights & Findings", expanded=True):
                        # Show summary if available
                        if insights.get('summary'):
                            st.markdown(f"**Summary:** {insights['summary']}")
                            st.markdown("---")

                        # Top findings
                        if insights.get('top_findings'):
                            st.markdown("**📊 Top Findings:**")
                            for finding in insights['top_findings']:
                                st.markdown(f"- {finding}")
                            st.markdown("")

                        # Trends
                        if insights.get('trends'):
                            st.markdown("**📈 Trends & Patterns:**")
                            for trend in insights['trends']:
                                st.markdown(f"- {trend}")
                            st.markdown("")

                        # Outliers
                        if insights.get('outliers'):
                            st.markdown("**⚠️ Outliers & Anomalies:**")
                            for outlier in insights['outliers']:
                                st.markdown(f"- {outlier}")
                            st.markdown("")

                        # Recommendations
                        if insights.get('recommendations'):
                            st.markdown("**💡 Recommendations:**")
                            for rec in insights['recommendations']:
                                st.markdown(f"- {rec}")

            # Display Phase 2 features: Validation & Confidence
            validation = metadata.get('validation')
            confidence_details = metadata.get('confidence_details')

            if validation or confidence_details:
                with st.expander("🎯 Confidence & Validation Details", expanded=False):
                    if confidence_details and isinstance(confidence_details, dict):
                        # Show confidence level with color coding
                        level = confidence_details.get('level', 'medium')
                        overall = confidence_details.get('overall', 0.0)
                        message = confidence_details.get('message', '')

                        if level == 'high':
                            st.success(f"{message} (Score: {overall:.2f})")
                        elif level == 'medium':
                            st.info(f"{message} (Score: {overall:.2f})")
                        else:
                            st.warning(f"{message} (Score: {overall:.2f})")

                        # Show confidence breakdown
                        st.markdown("**Confidence Breakdown:**")
                        cols = st.columns(4)
                        with cols[0]:
                            st.metric("Schema Match", f"{confidence_details.get('schema_match', 0):.2f}")
                        with cols[1]:
                            st.metric("Result Quality", f"{confidence_details.get('result_quality', 0):.2f}")
                        with cols[2]:
                            st.metric("Validation", f"{confidence_details.get('validation_score', 0):.2f}")
                        with cols[3]:
                            st.metric("Context Usage", f"{confidence_details.get('context_usage', 0):.2f}")

                    if validation and isinstance(validation, dict):
                        st.markdown("---")
                        st.markdown("**Validation Details:**")

                        # Show validation status
                        is_valid = validation.get('is_valid', True)
                        val_confidence = validation.get('confidence', 0.0)

                        if is_valid:
                            st.markdown(f"✅ Response validated (Confidence: {val_confidence:.2f})")
                        else:
                            st.markdown(f"⚠️ Response has concerns (Confidence: {val_confidence:.2f})")

                        # Show issues if present
                        issues = validation.get('issues', [])
                        if issues:
                            st.markdown("**Issues Found:**")
                            for issue in issues:
                                st.markdown(f"- {issue}")

                        # Show validation suggestions
                        val_suggestions = validation.get('suggestions', [])
                        if val_suggestions:
                            st.markdown("**Validation Suggestions:**")
                            for suggestion in val_suggestions:
                                st.markdown(f"- {suggestion}")

            # Only show warnings/suggestions if they exist and aren't already in content
            warnings = metadata.get('warnings')
            if warnings and len(warnings) > 0:
                for warning in warnings:
                    st.warning(warning)

            suggestions = metadata.get('suggestions')
            if suggestions and len(suggestions) > 0:
                st.info(f"💡 Suggestions: {', '.join(suggestions)}")


def get_available_chart_types(df: pd.DataFrame) -> list:
    """Determine which chart types are suitable for the given dataframe."""
    available_charts = []

    # Get column information
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    all_cols = df.columns.tolist()
    num_rows = len(df)
    num_numeric = len(numeric_cols)
    num_cols = len(all_cols)

    # Only show charts if we have actual data to visualize
    if num_rows == 0:
        return ["Table"]

    # Bar Chart: needs at least 1 numeric column and more than 1 row for meaningful visualization
    if num_numeric >= 1 and num_rows > 1:
        available_charts.append("Bar Chart")

    # Stacked Bar: needs at least 1 numeric column and more than 1 row
    if num_numeric >= 1 and num_rows > 1:
        available_charts.append("Stacked Bar")

    # Line Chart: needs at least 1 numeric column and more than 1 row (useful for time series)
    if num_numeric >= 1 and num_rows > 1:
        available_charts.append("Line Chart")

    # Scatter Plot: needs at least 2 numeric columns and more than 1 row
    if num_numeric >= 2 and num_rows > 1:
        available_charts.append("Scatter Plot")

    # Pie Chart: needs at least 1 numeric column, at least 2 total columns, and multiple rows
    if num_numeric >= 1 and num_cols >= 2 and num_rows > 1:
        available_charts.append("Pie Chart")

    # Treemap: needs at least 2 columns and more than 1 row
    if num_cols >= 2 and num_rows > 1:
        available_charts.append("Treemap")

    # Table: always available as fallback
    available_charts.append("Table")

    return available_charts


def create_chart(df: pd.DataFrame, unique_id: str = "") -> None:
    """Create interactive chart from dataframe."""
    st.subheader("📊 Visualize Data")

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    all_cols = df.columns.tolist()

    # Get available chart types based on data structure
    available_charts = get_available_chart_types(df)

    # Show info about why certain charts might not be available
    if len(available_charts) == 1 and available_charts[0] == "Table":
        if len(df) == 0:
            st.info("ℹ️ No data to visualize. Showing table only.")
        elif len(df) == 1:
            st.info("ℹ️ Single row results are best viewed as a table. Charts require multiple rows for meaningful visualization.")
        elif len(numeric_cols) == 0:
            st.info("ℹ️ No numeric columns found. Charts require at least one numeric column. Showing table only.")

    # Chart type selection - only show available options
    chart_type = st.selectbox(
        "Chart Type",
        available_charts,
        key=f"chart_type_{unique_id}"
    )

    if chart_type == "Bar Chart" and len(numeric_cols) >= 1:
        x_col = st.selectbox("X-axis", all_cols, key=f"bar_x_{unique_id}")
        y_col = st.selectbox("Y-axis", numeric_cols, key=f"bar_y_{unique_id}")

        fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Stacked Bar" and len(numeric_cols) >= 1:
        x_col = st.selectbox("X-axis", all_cols, key=f"stacked_x_{unique_id}")
        y_col = st.selectbox("Y-axis", numeric_cols, key=f"stacked_y_{unique_id}")

        # Optional: Group/stack by another column
        categorical_cols = [col for col in all_cols if col not in numeric_cols]
        if len(categorical_cols) > 1:
            color_col = st.selectbox("Stack by (optional)", [None] + categorical_cols, key=f"stacked_color_{unique_id}")
        else:
            color_col = None

        if color_col:
            fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=f"{y_col} by {x_col} (stacked by {color_col})", barmode='stack')
        else:
            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}", barmode='stack')
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Line Chart" and len(numeric_cols) >= 1:
        x_col = st.selectbox("X-axis", all_cols, key=f"line_x_{unique_id}")
        y_col = st.selectbox("Y-axis", numeric_cols, key=f"line_y_{unique_id}")

        fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Scatter Plot" and len(numeric_cols) >= 2:
        x_col = st.selectbox("X-axis", numeric_cols, key=f"scatter_x_{unique_id}")
        y_col = st.selectbox("Y-axis", numeric_cols, key=f"scatter_y_{unique_id}")

        fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Pie Chart":
        label_col = st.selectbox("Labels", all_cols, key=f"pie_labels_{unique_id}")
        value_col = st.selectbox("Values", numeric_cols, key=f"pie_values_{unique_id}") if numeric_cols else all_cols[0]

        fig = px.pie(df, names=label_col, values=value_col, title=f"Distribution of {value_col}")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Treemap" and len(all_cols) >= 2:
        st.info("💡 Treemap works best with hierarchical data (e.g., category → subcategory → value)")

        # Select path columns (hierarchical structure)
        if len(all_cols) >= 3:
            path_col1 = st.selectbox("First level (e.g., Category)", all_cols, key=f"treemap_path1_{unique_id}")
            remaining_cols = [col for col in all_cols if col != path_col1]
            path_col2 = st.selectbox("Second level (e.g., Subcategory)", remaining_cols, key=f"treemap_path2_{unique_id}")
            path_cols = [path_col1, path_col2]
        else:
            # Single level treemap
            path_col = st.selectbox("Category", all_cols, key=f"treemap_path_{unique_id}")
            path_cols = [path_col]

        # Select value column
        if numeric_cols:
            value_col = st.selectbox("Values (size)", numeric_cols, key=f"treemap_values_{unique_id}")
        else:
            st.warning("⚠️ No numeric columns found. Treemap will use count.")
            value_col = None

        try:
            if value_col:
                fig = px.treemap(df, path=path_cols, values=value_col, title=f"Treemap of {value_col}")
            else:
                # Count-based treemap when no numeric column
                fig = px.treemap(df, path=path_cols, title=f"Treemap of {path_cols[0]}")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Could not create treemap: {str(e)}")
            st.dataframe(df, use_container_width=True)

    else:
        st.dataframe(df, use_container_width=True)


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Get or create an event loop for the session.

    This fixes the "got Future attached to a different loop" error by
    ensuring all async operations in a session use the same event loop.
    """
    if 'event_loop' not in st.session_state:
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # No event loop or it's closed, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        st.session_state.event_loop = loop

    return st.session_state.event_loop


def run_async(coro) -> Any:
    """
    Run async coroutine with proper event loop handling for Streamlit.

    This uses a session-specific event loop to ensure all async operations
    (including asyncpg database connections) use the same loop.
    """
    loop = get_or_create_event_loop()
    return loop.run_until_complete(coro)


def main() -> None:
    """Main application."""
    init_session_state()

    # Auto-initialize on first load
    if not st.session_state.initialized:
        with st.spinner("🚀 Initializing..."):
            try:
                run_async(st.session_state.assistant.initialize())
                st.session_state.initialized = True
            except Exception as e:
                st.error(f"❌ Failed to initialize: {str(e)}")
                st.stop()

    # Welcome message and examples (only show if no messages and no current question)
    if len(st.session_state.messages) == 0 and not st.session_state.get('current_question'):
        st.markdown("""
        <div class="welcome-message">
            <h2>Ask questions about your crypto data</h2>
            <p>I can help you explore and analyze cryptocurrency prices, trading volumes, holdings, and revenue using natural language.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### Try asking:")

        # Example queries in a grid
        col1, col2 = st.columns(2)
        examples = [
            "What was Bitcoin's highest price in 2024?",
            "Show top 10 tokens by trading volume",
            "What's Ethereum's price trend over the last 6 months?",
            "How much revenue was generated from staking last month?",
            "Which users have the largest crypto holdings?",
            "Show me total trading volume by month for the last year"
        ]

        for idx, example in enumerate(examples):
            with col1 if idx % 2 == 0 else col2:
                if st.button(f"💬 {example}", key=f"ex_{idx}", use_container_width=True):
                    st.session_state.current_question = example
                    st.rerun()

    # Display chat messages
    if len(st.session_state.messages) > 0:
        # Add clear button at top when there are messages
        col1, col2, col3 = st.columns([1, 1, 6])
        with col1:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

        st.markdown("---")

    # Check if any insights were requested
    for idx, message in enumerate(st.session_state.messages):
        if message['role'] == 'assistant' and message.get('metadata'):
            metadata = message['metadata']
            timestamp = metadata.get('timestamp', '')

            # Check if insights were requested for this message
            if st.session_state.get(f'request_insights_{timestamp}'):
                # Generate insights
                with st.spinner("💎 Generating key takeaways and recommendations..."):
                    insights = run_async(st.session_state.assistant.orchestrator.generate_insights_for_response(
                        question=metadata.get('question', ''),
                        sql=metadata.get('sql', ''),
                        results=metadata.get('results', []),
                        conversation_history=st.session_state.messages[:idx]
                    ))

                    # Update message metadata with insights
                    st.session_state.messages[idx]['metadata']['insights'] = insights

                    # Clear the request flag
                    del st.session_state[f'request_insights_{timestamp}']
                    st.rerun()

    for message in st.session_state.messages:
        display_message(message['role'], message['content'], message.get('metadata'))

    # Input area
    if len(st.session_state.messages) > 0:
        st.markdown("---")

    # Handle example question
    default_question = st.session_state.get('current_question', '')
    if default_question:
        question = default_question
        st.session_state.current_question = None
    else:
        question = st.chat_input("Ask a question about your data...")

    if question:
        # Add user message
        st.session_state.messages.append({
            'role': 'user',
            'content': question
        })

        # Display user message immediately
        display_message('user', question, None)

        # Show thinking status below the question
        thinking_placeholder = st.empty()
        with thinking_placeholder:
            st.info("🤔 Thinking...")

        # Get or create session_id for context management
        if 'session_id' not in st.session_state:
            import hashlib
            import time
            st.session_state.session_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:16]

        # Get conversation history (exclude the current question, which was just added)
        conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []

        # Process question with conversation context and session_id
        response = run_async(st.session_state.assistant.process_question(
            question=question,
            session_id=st.session_state.session_id,
            conversation_history=conversation_history
        ))

        # Clear thinking message
        thinking_placeholder.empty()

        # Prepare assistant message
        if response['success']:
            content = response.get('explanation', '✅ Query executed successfully!')
            # For successful queries, show warnings separately (like result warnings)
            metadata = {
                'question': question,  # Store question for insights generation
                'sql': response.get('sql'),
                'results': response.get('results'),
                'warnings': response.get('warnings'),
                'suggestions': response.get('suggestions'),
                'insights': response.get('insights'),  # Will be None initially
                'timestamp': datetime.now().isoformat()
            }
        else:
            # For errors, build a clean combined message
            error_parts = ["❌ Could not answer this question."]

            warnings = response.get('warnings', [])
            suggestions = response.get('suggestions', [])

            if warnings:
                error_parts.append("\n\n**Error Details:**")
                for warning in warnings:
                    # Clean up the warning message
                    clean_warning = warning.replace("❌ ", "").replace("⚠️ ", "")
                    error_parts.append(f"- {clean_warning}")

            if suggestions:
                error_parts.append("\n\n**💡 Did you mean:**")
                for suggestion in suggestions[:5]:  # Limit to top 5
                    error_parts.append(f"- {suggestion}")

            content = "\n".join(error_parts)

            # Don't include warnings/suggestions in metadata for errors (already in content)
            metadata = {
                'sql': response.get('sql') if response.get('sql') else None,
                'results': None,
                'warnings': None,  # Already included in content
                'suggestions': None,  # Already included in content
                'timestamp': datetime.now().isoformat()
            }

        st.session_state.messages.append({
            'role': 'assistant',
            'content': content,
            'metadata': metadata
        })

        st.rerun()


if __name__ == "__main__":
    main()
