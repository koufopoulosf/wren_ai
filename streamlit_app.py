"""
Wren AI Data Assistant - Streamlit Interface

Modern chat interface for querying data warehouse with natural language.
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
from vector_search import VectorSearch
from sql_generator import SQLGenerator
from schema_embedder import SchemaEmbedder
from result_validator import ResultValidator
from query_explainer import QueryExplainer

# Page config
st.set_page_config(
    page_title="Wren AI Data Assistant",
    page_icon="🤖",
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


class WrenAssistant:
    """Main application class."""

    def __init__(self):
        """Initialize AI assistant."""
        self.config = Config()
        self.vector_search = None
        self.sql_generator = None
        self.result_validator = None
        self.explainer = None
        self.initialized = False
        self.schema_embedded = False
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

        # Initialize vector search
        self.vector_search = VectorSearch(
            qdrant_host=self.config.QDRANT_HOST,
            qdrant_port=self.config.QDRANT_PORT,
            ollama_url=self.config.OLLAMA_URL,
            embedding_model=self.config.EMBEDDING_MODEL,
            collection_name=self.config.VECTOR_COLLECTION
        )

        # Initialize SQL generator
        self.sql_generator = SQLGenerator(
            anthropic_client=self.config.anthropic_client,
            vector_search=self.vector_search,
            db_config=db_config,
            model=self.config.ANTHROPIC_MODEL
        )

        # Check if schema is embedded, if not embed it
        collection_info = self.vector_search.get_collection_info()
        if collection_info.get('points_count', 0) == 0:
            logger.info("Schema not embedded yet, embedding now...")
            schema_embedder = SchemaEmbedder(db_config, self.vector_search)
            await schema_embedder.refresh_schema_embeddings()
            self.schema_embedded = True
            logger.info("✅ Schema embedded successfully")
        else:
            logger.info(f"✅ Schema already embedded ({collection_info.get('points_count')} entities)")

        # Load schema info for display
        schema_embedder = SchemaEmbedder(db_config, self.vector_search)
        await schema_embedder.connect()
        try:
            self.schema_info = await schema_embedder.introspect_schema()
        finally:
            await schema_embedder.disconnect()

        # Initialize validators
        self.result_validator = ResultValidator(
            max_rows_warning=self.config.MAX_ROWS_DISPLAY
        )

        # Initialize explainer
        self.explainer = QueryExplainer(
            anthropic_client=self.config.anthropic_client,
            model=self.config.ANTHROPIC_MODEL
        )

        self.initialized = True

    async def classify_question(self, question: str) -> Dict[str, Any]:
        """
        Classify whether the question is about the data or about the system.

        Returns:
            {
                'is_data_query': bool,
                'response': str (only if not a data query)
            }
        """
        try:
            classification_prompt = f"""Analyze this user question and determine if it's asking about data in a database or if it's a meta/system question.

User question: "{question}"

A DATA QUERY asks about information stored in database tables (customers, orders, products, revenue, etc.)
Examples of DATA QUERIES:
- "What was total revenue last month?"
- "Show me top customers"
- "How many orders do we have?"
- "What's the average order value?"

A META/SYSTEM QUESTION asks about the AI system itself, its capabilities, or is unrelated to the database.
Examples of META/SYSTEM QUESTIONS:
- "Does the AI have access to data?"
- "What can you do?"
- "How does this work?"
- "What tables are available?"
- "Can you help me?"
- "What's the weather?"

Respond with JSON only:
{{
    "is_data_query": true/false,
    "explanation": "brief reason"
}}"""

            message = self.config.anthropic_client.messages.create(
                model=self.config.ANTHROPIC_MODEL,
                max_tokens=200,
                messages=[{"role": "user", "content": classification_prompt}]
            )

            response_text = message.content[0].text.strip()

            # Parse JSON response
            import json
            classification = json.loads(response_text)

            # If it's not a data query, generate a helpful response
            if not classification.get('is_data_query', True):
                # Generate natural language response
                response_prompt = f"""You are a helpful AI data assistant for an e-commerce analytics database.

The user asked: "{question}"

This is a question about the system/capabilities, not a data query. Provide a brief, friendly response.

Available data:
- E-commerce database with customers, orders, products, categories
- Sample data from January-April 2024
- Can answer questions about revenue, customers, orders, products, etc.

Keep your response concise (2-3 sentences) and helpful."""

                response_message = self.config.anthropic_client.messages.create(
                    model=self.config.ANTHROPIC_MODEL,
                    max_tokens=300,
                    messages=[{"role": "user", "content": response_prompt}]
                )

                return {
                    'is_data_query': False,
                    'response': response_message.content[0].text.strip()
                }

            return {'is_data_query': True}

        except Exception as e:
            logger.warning(f"Question classification failed: {e}, treating as data query")
            return {'is_data_query': True}

    async def process_question(self, question: str) -> Dict[str, Any]:
        """
        Process user question and return results.

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
        response = {
            'success': False,
            'sql': '',
            'results': [],
            'explanation': '',
            'warnings': [],
            'suggestions': [],
            'confidence': 0.0
        }

        try:
            # First, classify the question
            classification = await self.classify_question(question)

            # If it's not a data query, return the natural language response
            if not classification.get('is_data_query', True):
                response['success'] = True
                response['explanation'] = classification.get('response', '')
                return response

            # Generate SQL using vector search + Claude
            result = await self.sql_generator.ask(question)

            sql = result.get('sql', '')
            results = result.get('results', [])
            context_used = result.get('context_used', [])

            response['sql'] = sql
            response['results'] = results
            response['confidence'] = 0.9 if context_used else 0.5  # High confidence if context found
            response['explanation'] = result.get('explanation', '')

            if not sql:
                response['warnings'].append("❌ Could not generate SQL for this question.")
                return response

            # Validate results
            has_warnings, warning_msg = self.result_validator.validate_results(results, sql)
            if has_warnings:
                response['warnings'].append(warning_msg)

            # Generate detailed explanation if needed
            if results:
                explanation = await self.explainer.explain_query(question, sql, results[:5])
                response['explanation'] = explanation

            response['success'] = True

        except Exception as e:
            response['warnings'].append(f"❌ Error: {str(e)}")

        return response


def init_session_state():
    """Initialize session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'assistant' not in st.session_state:
        st.session_state.assistant = WrenAssistant()

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


def create_chart(df: pd.DataFrame, unique_id: str = ""):
    """Create interactive chart from dataframe."""
    st.subheader("📊 Visualize Data")

    # Chart type selection
    chart_type = st.selectbox(
        "Chart Type",
        ["Bar Chart", "Stacked Bar", "Line Chart", "Scatter Plot", "Pie Chart", "Treemap", "Table"],
        key=f"chart_type_{unique_id}"
    )

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    all_cols = df.columns.tolist()

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
        with st.spinner("🚀 Initializing Wren AI..."):
            try:
                run_async(st.session_state.assistant.initialize())
                st.session_state.initialized = True
            except Exception as e:
                st.error(f"❌ Failed to initialize Wren AI: {str(e)}")
                st.stop()

    # Header
    st.title("🤖 Wren AI Data Assistant")
    st.markdown('<span class="status-badge">✓ Ready</span>', unsafe_allow_html=True)

    # Welcome message and examples (only show if no messages)
    if len(st.session_state.messages) == 0:
        st.markdown("""
        <div class="welcome-message">
            <h2>Ask questions about your data</h2>
            <p>I can help you explore and analyze your e-commerce data using natural language.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### Try asking:")

        # Example queries in a grid
        col1, col2 = st.columns(2)
        examples = [
            "What was total revenue last month?",
            "Show top 10 customers by orders",
            "How many active customers do we have?",
            "What's our average order value?",
            "Show revenue trends by month",
            "Which products sell the best?"
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

        # Process question
        with st.spinner("🤔 Thinking..."):
            response = run_async(st.session_state.assistant.process_question(question))

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
