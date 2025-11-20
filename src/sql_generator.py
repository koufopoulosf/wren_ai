"""
Simplified SQL generation using Claude.

Clean architecture:
- Directly calls Claude for SQL generation with full DDL
- No external Wren AI Service dependency
- No vector search, embeddings, or semantic matching
- Claude's excellent semantic understanding handles schema reasoning
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio
import asyncpg
import time
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class SQLGenerator:
    """Generate SQL from natural language using Claude."""

    def __init__(
        self,
        anthropic_client: Anthropic,
        db_config: Dict[str, str],
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize SQL generator.

        Args:
            anthropic_client: Anthropic API client
            db_config: Database connection config
            model: Claude model to use
        """
        self.anthropic = anthropic_client
        self.db_config = db_config
        self.model = model
        self._db_conn = None

        # Schema caching (5 minute TTL)
        self._schema_cache = None
        self._schema_cache_time = 0
        self._schema_cache_ttl = 300  # 5 minutes in seconds

        logger.info(f"SQLGenerator initialized with model: {model}")

    async def connect_db(self):
        """Connect to database for SQL execution."""
        if not self._db_conn:
            self._db_conn = await asyncpg.connect(
                host=self.db_config.get("host", "localhost"),
                port=int(self.db_config.get("port", 5432)),
                database=self.db_config.get("database"),
                user=self.db_config.get("user"),
                password=self.db_config.get("password"),
                ssl=self.db_config.get("ssl", "disable")
            )
            logger.info("Connected to database")

    async def disconnect_db(self):
        """Disconnect from database."""
        if self._db_conn:
            await self._db_conn.close()
            self._db_conn = None
            logger.info("Disconnected from database")

    async def get_schema_ddl(self, force_refresh: bool = False) -> str:
        """
        Get schema as DDL (CREATE TABLE statements) with caching.

        Args:
            force_refresh: If True, bypass cache and fetch fresh schema

        Returns:
            DDL string for all tables
        """
        # Check cache first (unless force refresh)
        current_time = time.time()
        cache_age = current_time - self._schema_cache_time

        if not force_refresh and self._schema_cache and cache_age < self._schema_cache_ttl:
            logger.info(f"Using cached schema (age: {cache_age:.1f}s, TTL: {self._schema_cache_ttl}s)")
            return self._schema_cache

        # Cache miss or expired - fetch from database
        logger.info("Fetching fresh schema from database...")
        await self.connect_db()

        # Get all table definitions
        tables_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """

        tables = await self._db_conn.fetch(tables_query)
        ddl_parts = []

        for table_row in tables:
            table_name = table_row["table_name"]

            # Get columns
            columns_query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = $1
            ORDER BY ordinal_position
            """

            columns = await self._db_conn.fetch(columns_query, table_name)

            # Build CREATE TABLE
            col_defs = []
            for col in columns:
                nullable = "" if col["is_nullable"] == "YES" else " NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col["column_default"] else ""
                col_defs.append(
                    f"  {col['column_name']} {col['data_type']}{nullable}{default}"
                )

            ddl = f"CREATE TABLE {table_name} (\n" + ",\n".join(col_defs) + "\n);"
            ddl_parts.append(ddl)

        schema_ddl = "\n\n".join(ddl_parts)

        # Update cache
        self._schema_cache = schema_ddl
        self._schema_cache_time = current_time
        logger.info(f"Schema cached (TTL: {self._schema_cache_ttl}s)")

        return schema_ddl

    async def generate_sql(
        self,
        question: str,
        context_limit: int = 5,
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        Generate SQL from natural language question with conversation context.

        Args:
            question: User's natural language question
            context_limit: Max number of schema entities to include
            conversation_history: List of previous messages for context (optional)

        Returns:
            Dict with keys: sql, explanation, context_used
        """
        try:
            # 1. Get full schema DDL
            logger.info(f"Generating SQL for: {question}")
            schema_ddl = await self.get_schema_ddl()

            # 2. Build conversation context (if available)
            conversation_context = ""
            if conversation_history and len(conversation_history) > 0:
                # Include last 5 messages for context (to avoid token limits)
                recent_history = conversation_history[-5:]
                history_parts = []
                for msg in recent_history:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    # Truncate long content to avoid bloat
                    if len(content) > 300:
                        content = content[:300] + "..."
                    history_parts.append(f"{role.capitalize()}: {content}")

                conversation_context = f"""

## Recent Conversation History
{chr(10).join(history_parts)}

Note: The user's current question may reference this conversation history. Use it to understand context like follow-up questions (e.g., "yes please proceed", "show me more", "what about X?").
"""

            # 3. Build Claude prompt
            prompt = f"""You are a SQL expert. Generate a PostgreSQL query to answer the user's question.

## Database Schema (DDL)
{schema_ddl}{conversation_context}

## User Question
{question}

## Instructions
- Generate ONLY a SINGLE SQL query, no explanations
- Use PostgreSQL syntax
- Use appropriate JOINs, WHERE clauses, and aggregations
- Return ONLY the SQL query text
- Do not include markdown code blocks or backticks
- Do not use semicolons to separate multiple statements
- Generate exactly ONE SELECT/INSERT/UPDATE/DELETE statement
- Make sure the query is valid and executable
- If the question references the conversation history (like "yes", "proceed", "show more"), interpret it in context
- If the question is too vague even with history, return the text "AMBIGUOUS_QUERY" instead of SQL

SQL Query:"""

            # 4. Call Claude
            logger.info("Calling Claude to generate SQL...")
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            )

            sql = message.content[0].text.strip()

            # Clean up SQL (remove markdown if present)
            if sql.startswith("```"):
                sql = "\n".join(sql.split("\n")[1:-1])
                sql = sql.strip()

            # Check if Claude indicated the query is ambiguous
            if "AMBIGUOUS_QUERY" in sql:
                logger.warning("Claude detected ambiguous query")
                raise ValueError("Your question is too vague. Please be more specific or provide more details about what you want to know.")

            # Handle multiple statements: take only the last non-empty statement
            # This prevents "cannot insert multiple commands into a prepared statement" error
            if ';' in sql:
                statements = [s.strip() for s in sql.split(';') if s.strip()]
                if statements:
                    sql = statements[-1]  # Use the last statement
                    logger.warning(f"Multiple SQL statements detected, using only the last one")

            logger.info(f"Generated SQL: {sql[:100]}...")

            return {
                "sql": sql,
                "explanation": "Generated SQL using full schema DDL",
                "context_used": []
            }

        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise

    async def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.

        Args:
            sql: SQL query to execute

        Returns:
            List of row dicts
        """
        try:
            await self.connect_db()

            logger.info(f"Executing SQL: {sql[:100]}...")
            rows = await self._db_conn.fetch(sql)

            # Convert to list of dicts
            results = [dict(row) for row in rows]

            logger.info(f"Query returned {len(results)} rows")
            return results

        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            raise

    async def ask(self, question: str, conversation_history: list = None) -> Dict[str, Any]:
        """
        Full pipeline: generate SQL from question and execute it.

        Args:
            question: User's natural language question
            conversation_history: List of previous messages for context (optional)

        Returns:
            Dict with keys: question, sql, results, explanation
        """
        try:
            # Generate SQL with conversation context
            generation_result = await self.generate_sql(
                question,
                conversation_history=conversation_history
            )
            sql = generation_result["sql"]

            # Execute SQL
            results = await self.execute_sql(sql)

            return {
                "question": question,
                "sql": sql,
                "results": results,
                "explanation": generation_result["explanation"],
                "context_used": generation_result["context_used"]
            }

        except Exception as e:
            logger.error(f"Error in ask pipeline: {e}")
            raise
