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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Claude-like aesthetics
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Keep header visible for sidebar toggle */
    header[data-testid="stHeader"] {
        background-color: transparent;
    }

    /* Main container */
    .main {
        background-color: #ffffff;
        max-width: 1200px;
        padding: 2rem 1rem;
    }

    .block-container {
        padding-top: 1rem;
        max-width: 1200px;
    }

    /* Chat message styling - Claude-like */
    .user-message {
        background-color: #f7f7f8;
        padding: 16px 24px;
        border-radius: 16px;
        margin: 16px 0;
        font-size: 15px;
        line-height: 1.6;
        color: #2c3e50;
    }

    .assistant-message {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 16px 24px;
        border-radius: 16px;
        margin: 16px 0;
        font-size: 15px;
        line-height: 1.7;
        color: #1f2937;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Code blocks - like Claude */
    .stCodeBlock {
        background-color: #f6f8fa;
        border-radius: 8px;
        border: 1px solid #d0d7de;
    }

    /* Buttons - minimal and clean */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #d0d7de;
        padding: 8px 16px;
        transition: all 0.2s;
        background-color: #ffffff;
        color: #24292f;
        font-weight: 500;
    }

    .stButton>button:hover {
        background-color: #f6f8fa;
        border-color: #2ea44f;
    }

    .stButton>button[kind="primary"] {
        background-color: #2ea44f;
        color: white;
        border: none;
    }

    .stButton>button[kind="primary"]:hover {
        background-color: #2c974b;
    }

    /* Chat input - clean and modern */
    .stChatInput {
        border-radius: 12px;
        border: 2px solid #d0d7de;
        padding: 12px 16px;
        font-size: 15px;
    }

    .stChatInput:focus {
        border-color: #2ea44f;
        box-shadow: 0 0 0 3px rgba(46, 164, 79, 0.1);
    }

    /* Sidebar - clean */
    [data-testid="stSidebar"] {
        background-color: #f7f7f8;
        border-right: 1px solid #e5e7eb;
    }

    [data-testid="stSidebar"] .element-container {
        padding: 0.5rem 0;
    }

    /* Metrics - simple cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
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
    }

    h2, h3 {
        font-weight: 600;
        color: #374151;
    }

    /* Dataframe styling */
    .dataframe {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
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
        st.markdown(f'<div class="user-message">👤 {content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">🤖 {content}</div>', unsafe_allow_html=True)

        # Display metadata if present
        if metadata:
            if metadata.get('sql'):
                with st.expander("📝 View SQL"):
                    st.code(metadata['sql'], language='sql')

            if metadata.get('results'):
                results = metadata['results']
                df = pd.DataFrame(results)

                with st.expander(f"📊 View Results ({len(results)} rows)"):
                    st.dataframe(df, use_container_width=True)

                    # Export options
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv",
                            key=f"csv_{metadata.get('timestamp', '')}"
                        )

                    with col2:
                        json_str = df.to_json(orient='records', indent=2)
                        st.download_button(
                            "📥 Download JSON",
                            json_str,
                            f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            "application/json",
                            key=f"json_{metadata.get('timestamp', '')}"
                        )

                    with col3:
                        if st.button("📈 Create Chart", key=f"chart_{metadata.get('timestamp', '')}"):
                            st.session_state[f'show_chart_{metadata.get("timestamp", "")}'] = True

                # Show chart if requested
                if st.session_state.get(f'show_chart_{metadata.get("timestamp", "")}'):
                    create_chart(df)

            # Only show warnings/suggestions if they exist and aren't already in content
            warnings = metadata.get('warnings')
            if warnings and len(warnings) > 0:
                for warning in warnings:
                    st.warning(warning)

            suggestions = metadata.get('suggestions')
            if suggestions and len(suggestions) > 0:
                st.info(f"💡 Suggestions: {', '.join(suggestions)}")


def create_chart(df: pd.DataFrame):
    """Create interactive chart from dataframe."""
    st.subheader("📊 Visualize Data")

    # Chart type selection
    chart_type = st.selectbox(
        "Chart Type",
        ["Bar Chart", "Line Chart", "Scatter Plot", "Pie Chart", "Table"]
    )

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    all_cols = df.columns.tolist()

    if chart_type == "Bar Chart" and len(numeric_cols) >= 1:
        x_col = st.selectbox("X-axis", all_cols)
        y_col = st.selectbox("Y-axis", numeric_cols)

        fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Line Chart" and len(numeric_cols) >= 1:
        x_col = st.selectbox("X-axis", all_cols)
        y_col = st.selectbox("Y-axis", numeric_cols)

        fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Scatter Plot" and len(numeric_cols) >= 2:
        x_col = st.selectbox("X-axis", numeric_cols)
        y_col = st.selectbox("Y-axis", numeric_cols)

        fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Pie Chart":
        label_col = st.selectbox("Labels", all_cols)
        value_col = st.selectbox("Values", numeric_cols) if numeric_cols else all_cols[0]

        fig = px.pie(df, names=label_col, values=value_col, title=f"Distribution of {value_col}")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.dataframe(df, use_container_width=True)


async def main():
    """Main application."""
    init_session_state()

    # Auto-initialize on first load
    if not st.session_state.initialized:
        with st.spinner("🚀 Initializing Wren AI..."):
            try:
                await st.session_state.assistant.initialize()
                st.session_state.initialized = True
            except Exception as e:
                st.error(f"❌ Failed to initialize Wren AI: {str(e)}")
                st.stop()

    # Header with sidebar toggle
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("🤖 Wren AI Data Assistant")
        st.markdown("Ask questions about your data in natural language")
    with col2:
        # Sidebar toggle button
        if st.button("☰", key="sidebar_toggle", help="Toggle sidebar"):
            st.rerun()

    # Sidebar
    with st.sidebar:
        st.success("✅ Wren AI Ready")

        st.markdown("---")

        # Statistics
        st.subheader("📊 Schema Info")
        schema_info = st.session_state.assistant.schema_info
        tables = schema_info.get("tables", [])
        relationships = schema_info.get("relationships", [])

        # Get unique table names
        table_names = list(set([t.get("table_name") for t in tables if t.get("table_name")]))

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tables", len(table_names))
        with col2:
            st.metric("Relationships", len(relationships))

        # Show message if no schema loaded
        if len(table_names) == 0:
            st.warning("""
            ⚠️ **No schema loaded**

            **Possible causes:**
            - Database not connected (check `.env` file)
            - Invalid database credentials
            - Database has no tables in the 'public' schema
            - Qdrant or Ollama services not running

            **To fix:**
            1. Copy `.env.example` to `.env`
            2. Set your `ANTHROPIC_API_KEY`
            3. Set your database credentials:
               - `DB_HOST`, `DB_PORT`, `DB_DATABASE`
               - `DB_USER`, `DB_PASSWORD`
            4. Ensure Qdrant and Ollama services are running
            5. Restart the app

            **Or:** Use Docker Compose for auto-setup:
            ```
            docker-compose up -d
            ```
            """)

            # Show current config (masked passwords)
            with st.expander("🔍 View Current Config"):
                st.code(f"""
Database Type: {st.session_state.assistant.config.DB_TYPE}
Database Host: {st.session_state.assistant.config.DB_HOST}
Database Port: {st.session_state.assistant.config.DB_PORT}
Database Name: {st.session_state.assistant.config.DB_DATABASE}
Database User: {st.session_state.assistant.config.DB_USER}
Qdrant Host: {st.session_state.assistant.config.QDRANT_HOST}
Ollama URL: {st.session_state.assistant.config.OLLAMA_URL}
                """, language="yaml")

        # Show available tables
        if table_names:
            with st.expander("📋 View Tables", expanded=False):
                # Group columns by table
                tables_dict = {}
                for table_row in tables:
                    table_name = table_row.get("table_name")
                    if table_name not in tables_dict:
                        tables_dict[table_name] = {
                            "comment": table_row.get("table_comment"),
                            "columns": []
                        }
                    tables_dict[table_name]["columns"].append({
                        "name": table_row.get("column_name"),
                        "type": table_row.get("data_type"),
                        "nullable": table_row.get("is_nullable")
                    })

                for table_name in sorted(tables_dict.keys()):
                    table_info = tables_dict[table_name]
                    comment = table_info.get("comment")
                    column_count = len(table_info.get("columns", []))

                    if comment:
                        st.write(f"**{table_name}** ({column_count} columns)")
                        st.caption(comment)
                    else:
                        st.write(f"• **{table_name}** ({column_count} columns)")

        st.markdown("---")

        # Example queries
        st.subheader("💡 Example Queries")
        examples = [
            "What was total revenue last month?",
            "Show top 10 customers by orders",
            "How many active customers do we have?",
            "What's our average order value?",
            "Show revenue trends by month"
        ]

        for example in examples:
            if st.button(example, key=f"ex_{example}", use_container_width=True):
                st.session_state.current_question = example
                st.rerun()

        st.markdown("---")

        # Clear chat
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Display chat messages
    for message in st.session_state.messages:
        display_message(message['role'], message['content'], message.get('metadata'))

    # Input area
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
            response = await st.session_state.assistant.process_question(question)

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
    asyncio.run(main())
