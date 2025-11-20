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
from sql_generator import SQLGenerator
from result_validator import ResultValidator
from query_explainer import QueryExplainer
from question_classifier import QuestionClassifier
from response_generator import ResponseGenerator
from pipeline_orchestrator import PipelineOrchestrator

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
        transition: all 0.15s ease;
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
        transition: all 0.15s ease;
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

    Note: Renamed from WrenAssistant to avoid confusion - we don't use Wren AI.
    """

    def __init__(self):
        """Initialize data assistant."""
        self.config = Config()
        self.sql_generator = None
        self.result_validator = None
        self.explainer = None
        self.classifier = None
        self.response_generator = None
        self.orchestrator = None
        self.initialized = False
        self.schema_info = {"tables": [], "relationships": []}

    async def initialize(self):
        """Initialize async components."""
        if self.initialized:
            return

        # Database config
        db_config = {
            "host": self.config.DB_HOST,
            "port": self.config.DB_PORT,
            "database": self.config.DB_DATABASE,
            "user": self.config.DB_USER,
            "password": self.config.DB_PASSWORD,
            "ssl": "require" if self.config.DB_SSL else "disable"
        }

        # Initialize SQL generator (simplified - no vector search needed)
        self.sql_generator = SQLGenerator(
            anthropic_client=self.config.anthropic_client,
            db_config=db_config,
            model=self.config.ANTHROPIC_MODEL,
            db_type=self.config.DB_TYPE
        )

        # Load basic schema info for display
        await self.sql_generator.connect_db()
        try:
            # Get table names using public method (not accessing private attributes)
            table_names = await self.sql_generator.get_table_names()
            self.schema_info["tables"] = [{"name": name} for name in table_names]
            logger.info(f"✅ Loaded schema: {len(self.schema_info['tables'])} tables")
        except Exception as e:
            logger.warning(f"Could not load schema info: {e}")
            self.schema_info["tables"] = []

        # Initialize validators
        self.result_validator = ResultValidator(
            max_rows_warning=self.config.MAX_ROWS_DISPLAY
        )

        # Initialize explainer
        self.explainer = QueryExplainer(
            anthropic_client=self.config.anthropic_client,
            model=self.config.ANTHROPIC_MODEL
        )

        # Initialize new specialized components
        self.classifier = QuestionClassifier(
            anthropic_client=self.config.anthropic_client,
            model=self.config.ANTHROPIC_MODEL
        )

        self.response_generator = ResponseGenerator(
            anthropic_client=self.config.anthropic_client,
            model=self.config.ANTHROPIC_MODEL
        )

        # Initialize orchestrator with all components
        self.orchestrator = PipelineOrchestrator(
            classifier=self.classifier,
            response_generator=self.response_generator,
            sql_generator=self.sql_generator,
            result_validator=self.result_validator
        )

        self.initialized = True
        logger.info("✅ DataAssistant fully initialized with new architecture")

    async def process_question(self, question: str, conversation_history: list = None) -> Dict[str, Any]:
        """
        Process user question through the pipeline orchestrator.

        This method now delegates to the PipelineOrchestrator for all
        question processing logic, keeping DataAssistant focused on
        UI coordination.

        Args:
            question: User's natural language question
            conversation_history: List of previous messages for context (optional)

        Returns:
            {
                'success': bool,
                'sql': str,
                'results': List[Dict],
                'explanation': str,
                'warnings': List[str],
                'suggestions': List[str],
                'confidence': float
            }
        """
        # Delegate to orchestrator
        return await self.orchestrator.process(
            question=question,
            conversation_history=conversation_history
        )


def init_session_state():
    """Initialize session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'assistant' not in st.session_state:
        st.session_state.assistant = DataAssistant()

    if 'initialized' not in st.session_state:
        st.session_state.initialized = False


def display_message(role: str, content: str, metadata: Dict = None):
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

                    # Export options
                    col1, col2, col3 = st.columns(3)

                    with col1:
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
                        json_str = df.to_json(orient='records', indent=2)
                        st.download_button(
                            "⬇ JSON",
                            json_str,
                            f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            "application/json",
                            key=f"json_{metadata.get('timestamp', '')}",
                            use_container_width=True
                        )

                    with col3:
                        if st.button("📈 Chart", key=f"chart_{metadata.get('timestamp', '')}", use_container_width=True):
                            st.session_state[f'show_chart_{metadata.get("timestamp", "")}'] = True

                # Show chart if requested
                if st.session_state.get(f'show_chart_{metadata.get("timestamp", "")}'):
                    create_chart(df, unique_id=metadata.get("timestamp", ""))

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


def create_chart(df: pd.DataFrame, unique_id: str = ""):
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


def get_or_create_event_loop():
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


def run_async(coro):
    """
    Run async coroutine with proper event loop handling for Streamlit.

    This uses a session-specific event loop to ensure all async operations
    (including asyncpg database connections) use the same loop.
    """
    loop = get_or_create_event_loop()
    return loop.run_until_complete(coro)


def main():
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

        # Get conversation history (exclude the current question, which was just added)
        conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []

        # Process question with conversation context
        response = run_async(st.session_state.assistant.process_question(question, conversation_history=conversation_history))

        # Clear thinking message
        thinking_placeholder.empty()

        # Prepare assistant message
        if response['success']:
            content = response.get('explanation', '✅ Query executed successfully!')
            # For successful queries, show warnings separately (like result warnings)
            metadata = {
                'sql': response.get('sql'),
                'results': response.get('results'),
                'warnings': response.get('warnings'),
                'suggestions': response.get('suggestions'),
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
