"""
Auto-generate and embed PostgreSQL schema into vector database.

This module:
1. Introspects PostgreSQL schema (tables, columns, relationships)
2. Generates semantic descriptions for each entity
3. Embeds entities into Qdrant for semantic search

Replaces manual MDL (schema.json) with auto-discovery.
"""

import logging
from typing import List, Dict, Any, Optional
import asyncpg
from src.vector_search import VectorSearch

logger = logging.getLogger(__name__)


class SchemaEmbedder:
    """Auto-discover PostgreSQL schema and embed for semantic search."""

    def __init__(
        self,
        db_config: Dict[str, str],
        vector_search: VectorSearch
    ):
        """
        Initialize schema embedder.

        Args:
            db_config: PostgreSQL connection config
            vector_search: VectorSearch instance for embedding
        """
        self.db_config = db_config
        self.vector_search = vector_search
        self._conn = None

    async def connect(self):
        """Connect to PostgreSQL."""
        try:
            self._conn = await asyncpg.connect(
                host=self.db_config.get("host", "localhost"),
                port=int(self.db_config.get("port", 5432)),
                database=self.db_config.get("database"),
                user=self.db_config.get("user"),
                password=self.db_config.get("password"),
                ssl=self.db_config.get("ssl", "disable")
            )
            logger.info("Connected to PostgreSQL for schema introspection")
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            raise

    async def disconnect(self):
        """Disconnect from PostgreSQL."""
        if self._conn:
            await self._conn.close()
            logger.info("Disconnected from PostgreSQL")

    async def introspect_schema(self) -> Dict[str, Any]:
        """
        Introspect PostgreSQL schema.

        Returns:
            Dict with keys: tables, relationships
        """
        schema = {
            "tables": await self._get_tables(),
            "relationships": await self._get_relationships()
        }

        logger.info(f"Introspected schema: {len(schema['tables'])} tables, "
                   f"{len(schema['relationships'])} relationships")

        return schema

    async def _get_tables(self) -> List[Dict[str, Any]]:
        """Get all tables and their columns."""
        query = """
        SELECT
            t.table_name,
            obj_description(
                (quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))::regclass::oid
            ) AS table_comment,
            c.column_name,
            c.data_type,
            c.is_nullable,
            col_description(
                (quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))::regclass::oid,
                c.ordinal_position
            ) AS column_comment
        FROM information_schema.tables t
        JOIN information_schema.columns c
            ON t.table_name = c.table_name
            AND t.table_schema = c.table_schema
        WHERE t.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name, c.ordinal_position
        """

        rows = await self._conn.fetch(query)

        # Group by table
        tables_dict = {}
        for row in rows:
            table_name = row["table_name"]

            if table_name not in tables_dict:
                tables_dict[table_name] = {
                    "name": table_name,
                    "comment": row["table_comment"] or "",
                    "columns": []
                }

            tables_dict[table_name]["columns"].append({
                "name": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES",
                "comment": row["column_comment"] or ""
            })

        return list(tables_dict.values())

    async def _get_relationships(self) -> List[Dict[str, Any]]:
        """Get foreign key relationships."""
        query = """
        SELECT
            tc.table_name AS from_table,
            kcu.column_name AS from_column,
            ccu.table_name AS to_table,
            ccu.column_name AS to_column,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        """

        rows = await self._conn.fetch(query)

        relationships = []
        for row in rows:
            relationships.append({
                "from_table": row["from_table"],
                "from_column": row["from_column"],
                "to_table": row["to_table"],
                "to_column": row["to_column"],
                "name": row["constraint_name"]
            })

        return relationships

    def _build_table_description(
        self,
        table: Dict[str, Any],
        relationships: List[Dict[str, Any]]
    ) -> str:
        """
        Build semantic description for a table.

        Args:
            table: Table metadata
            relationships: All relationships

        Returns:
            Rich text description for embedding
        """
        parts = [f"Table: {table['name']}"]

        # Add table comment if exists
        if table.get("comment"):
            parts.append(f"Description: {table['comment']}")

        # Add column info
        column_names = [col["name"] for col in table["columns"]]
        parts.append(f"Columns: {', '.join(column_names)}")

        # Add relationships
        related_tables = set()
        for rel in relationships:
            if rel["from_table"] == table["name"]:
                related_tables.add(rel["to_table"])
            elif rel["to_table"] == table["name"]:
                related_tables.add(rel["from_table"])

        if related_tables:
            parts.append(f"Related to: {', '.join(related_tables)}")

        return ". ".join(parts)

    def _build_column_description(
        self,
        table_name: str,
        column: Dict[str, Any]
    ) -> str:
        """
        Build semantic description for a column.

        Args:
            table_name: Parent table name
            column: Column metadata

        Returns:
            Rich text description for embedding
        """
        parts = [
            f"Column: {table_name}.{column['name']}",
            f"Type: {column['type']}"
        ]

        if column.get("comment"):
            parts.append(f"Description: {column['comment']}")

        if not column["nullable"]:
            parts.append("Required field")

        return ". ".join(parts)

    async def embed_schema(self, clear_existing: bool = True):
        """
        Embed entire schema into vector database.

        Args:
            clear_existing: Whether to clear existing embeddings first
        """
        try:
            # Introspect schema
            schema = await self.introspect_schema()

            # Clear existing if requested
            if clear_existing:
                logger.info("Clearing existing embeddings...")
                self.vector_search.clear_collection()

            # Prepare entities for batch embedding
            entities = []

            # Embed tables
            for table in schema["tables"]:
                table_desc = self._build_table_description(table, schema["relationships"])
                entities.append({
                    "entity_id": f"table:{table['name']}",
                    "text": table_desc,
                    "entity_type": "table",
                    "metadata": {
                        "table_name": table["name"],
                        "column_count": len(table["columns"])
                    }
                })

                # Embed columns
                for column in table["columns"]:
                    col_desc = self._build_column_description(table["name"], column)
                    entities.append({
                        "entity_id": f"column:{table['name']}.{column['name']}",
                        "text": col_desc,
                        "entity_type": "column",
                        "metadata": {
                            "table_name": table["name"],
                            "column_name": column["name"],
                            "data_type": column["type"]
                        }
                    })

            # Batch embed all entities
            logger.info(f"Embedding {len(entities)} entities...")
            await self.vector_search.index_entities_batch(entities)

            logger.info(f"Successfully embedded schema: {len(schema['tables'])} tables, "
                       f"{len(entities)} total entities")

            # Log collection stats
            stats = self.vector_search.get_collection_info()
            logger.info(f"Collection stats: {stats}")

        except Exception as e:
            logger.error(f"Error embedding schema: {e}")
            raise

    async def refresh_schema_embeddings(self):
        """Convenience method to refresh all embeddings."""
        await self.connect()
        try:
            await self.embed_schema(clear_existing=True)
        finally:
            await self.disconnect()
