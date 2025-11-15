"""
Simplified SQL generation using Claude + Vector Search.

Replaces the complex WrenClient with a cleaner architecture:
- Uses vector search to find relevant schema elements
- Directly calls Claude for SQL generation
- No external Wren AI Service dependency
- No manual MDL, entity cache, or fuzzy matching
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio
import asyncpg
from anthropic import Anthropic
from src.vector_search import VectorSearch

logger = logging.getLogger(__name__)


class SQLGenerator:
    """Generate SQL from natural language using Claude + vector search."""

    def __init__(
        self,
        anthropic_client: Anthropic,
        vector_search: VectorSearch,
        db_config: Dict[str, str],
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize SQL generator.

        Args:
            anthropic_client: Anthropic API client
            vector_search: VectorSearch instance for semantic search
            db_config: Database connection config
            model: Claude model to use
        """
        self.anthropic = anthropic_client
        self.vector_search = vector_search
        self.db_config = db_config
        self.model = model
        self._db_conn = None

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

    async def get_schema_ddl(self) -> str:
        """
        Get schema as DDL (CREATE TABLE statements).

        Returns:
            DDL string for all tables
        """
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

        return "\n\n".join(ddl_parts)

    async def generate_sql(
        self,
        question: str,
        context_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Generate SQL from natural language question.

        Args:
            question: User's natural language question
            context_limit: Max number of schema entities to include

        Returns:
            Dict with keys: sql, explanation, context_used
        """
        try:
            # 1. Use vector search to find relevant schema entities
            logger.info(f"Searching for relevant schema for: {question}")
            context_matches = await self.vector_search.search(
                query=question,
                limit=context_limit,
                score_threshold=0.3  # Lower threshold for more results
            )

            # 2. Build context from vector search results
            context_parts = []
            for match in context_matches:
                context_parts.append(
                    f"- {match['text']} (relevance: {match['score']:.2f})"
                )

            schema_context = "\n".join(context_parts) if context_parts else "No specific schema context found"

            # 3. Get full schema DDL
            schema_ddl = await self.get_schema_ddl()

            # 4. Build Claude prompt
            prompt = f"""You are a SQL expert. Generate a PostgreSQL query to answer the user's question.

## Database Schema (DDL)
{schema_ddl}

## Relevant Schema Context (from semantic search)
{schema_context}

## User Question
{question}

## Instructions
- Generate ONLY the SQL query, no explanations
- Use PostgreSQL syntax
- Use appropriate JOINs, WHERE clauses, and aggregations
- Return ONLY the SQL query text
- Do not include markdown code blocks or backticks
- Make sure the query is valid and executable

SQL Query:"""

            # 5. Call Claude
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

            logger.info(f"Generated SQL: {sql[:100]}...")

            return {
                "sql": sql,
                "explanation": f"Used {len(context_matches)} relevant schema entities",
                "context_used": context_matches
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

    async def ask(self, question: str) -> Dict[str, Any]:
        """
        Full pipeline: generate SQL from question and execute it.

        Args:
            question: User's natural language question

        Returns:
            Dict with keys: question, sql, results, explanation
        """
        try:
            # Generate SQL
            generation_result = await self.generate_sql(question)
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
