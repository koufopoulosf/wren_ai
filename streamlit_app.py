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
from wren_client import WrenClient
from validator import SQLValidator
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
    header {visibility: hidden;}
    .stDeployButton {display: none;}

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
        """Initialize Wren AI assistant."""
        self.config = Config()
        self.wren = None
        self.validator = None
        self.result_validator = None
        self.explainer = None
        self.initialized = False

    async def initialize(self):
        """Initialize async components."""
        if self.initialized:
            return

        # Initialize Wren AI client
        db_config = {
            "host": self.config.DB_HOST,
            "port": self.config.DB_PORT,
            "database": self.config.DB_DATABASE,
            "user": self.config.DB_USER,
            "password": self.config.DB_PASSWORD,
            "sslmode": "require" if self.config.DB_SSL else "prefer"
        }

        self.wren = WrenClient(
            base_url=self.config.WREN_URL,
            db_type=self.config.DB_TYPE,
            db_config=db_config,
            mdl_hash=self.config.WREN_MDL_HASH,
            anthropic_client=self.config.anthropic_client,
            model=self.config.ANTHROPIC_MODEL
        )

        # Load MDL (or fallback to database introspection)
        mdl_loaded = await self.wren.load_mdl()

        if not mdl_loaded:
            logger.warning("⚠️ Schema discovery incomplete - functionality may be limited")

        # Initialize validators
        self.validator = SQLValidator(
            mdl_models=self.wren._mdl_models,
            mdl_metrics=self.wren._mdl_metrics
        )

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
            # Step 1: Pre-validate entities
            is_valid, error_msg, suggestions = await self.wren.validate_question_entities(question)

            if not is_valid:
                response['warnings'].append(error_msg)
                response['suggestions'] = suggestions
                return response

            # Step 2: Get SQL from Wren AI
            wren_response = await self.wren.ask_question(question)

            sql = wren_response.get('sql', '')
            confidence = wren_response.get('confidence', 0.0)

            response['sql'] = sql
            response['confidence'] = confidence

            if not sql:
                response['warnings'].append("❌ Could not generate SQL for this question.")
                response['suggestions'] = wren_response.get('suggestions', [])
                return response

            # Step 3: Validate SQL
            is_valid, error_msg = self.validator.validate(sql)

            if not is_valid:
                response['warnings'].append(error_msg)
                return response

            # Step 4: Execute SQL
            results = await self.wren.execute_sql(sql)
            response['results'] = results

            # Step 5: Validate results
            has_warnings, warning_msg = self.result_validator.validate_results(results, sql)
            if has_warnings:
                response['warnings'].append(warning_msg)

            # Step 6: Generate explanation
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
        models = st.session_state.assistant.wren._mdl_models
        metrics = st.session_state.assistant.wren._mdl_metrics

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tables", len(models))
        with col2:
            st.metric("Metrics", len(metrics))

        # Show message if no schema loaded
        if len(models) == 0 and len(metrics) == 0:
            st.warning("""
            ⚠️ **No schema loaded**

            **Possible causes:**
            - Wren AI service not running (`WREN_URL`)
            - Database not connected (check `.env` file)
            - Invalid database credentials

            **To fix:**
            1. Copy `.env.example` to `.env`
            2. Set your `ANTHROPIC_API_KEY`
            3. Set your database credentials:
               - `DB_HOST`, `DB_PORT`, `DB_DATABASE`
               - `DB_USER`, `DB_PASSWORD`
            4. Restart the app

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
Wren AI URL: {st.session_state.assistant.config.WREN_URL}
                """, language="yaml")

        # Show available tables
        if models:
            with st.expander("📋 View Tables", expanded=False):
                for model in models:
                    name = model.get('name', 'Unknown')
                    desc = model.get('description', '')
                    if desc:
                        st.write(f"**{name}**")
                        st.caption(desc)
                    else:
                        st.write(f"• {name}")

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
