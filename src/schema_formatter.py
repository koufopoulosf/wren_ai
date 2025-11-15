"""
Schema Formatter - Dual Format Support

Provides two schema representations optimized for different use cases:
1. DDL Format - For SQL generation (matches database structure)
2. Markdown Format - For LLM reasoning (human-readable)

This improves SQL generation accuracy by presenting the schema in the most
effective format for each task.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SchemaFormatter:
    """Format MDL schema in different representations."""

    def __init__(self, mdl_models: List[Dict], mdl_metrics: List[Dict] = None):
        """
        Initialize formatter with MDL.

        Args:
            mdl_models: List of model definitions from MDL
            mdl_metrics: Optional list of metric definitions
        """
        self.models = mdl_models or []
        self.metrics = mdl_metrics or []

    def to_ddl(self, include_comments: bool = True, include_examples: bool = True) -> str:
        """
        Convert to PostgreSQL DDL format.

        Best for: SQL generation with code-specialized models

        Args:
            include_comments: Include column descriptions as comments
            include_examples: Include example values

        Returns:
            DDL-formatted schema string
        """
        ddl_parts = []

        for model in self.models:
            table_name = model.get('name', 'unknown')
            description = model.get('description', '')
            columns = model.get('columns', [])
            primary_key = model.get('primaryKey', '')
            relationships = model.get('relationships', [])

            # Table definition
            table_ddl = f"CREATE TABLE {table_name} (\n"

            # Columns
            col_definitions = []
            for col in columns:
                col_name = col.get('name', '')
                col_type = col.get('type', 'TEXT').upper()
                col_desc = col.get('description', '')

                # Map types to PostgreSQL
                type_map = {
                    'STRING': 'TEXT',
                    'VARCHAR': 'TEXT',
                    'INTEGER': 'INTEGER',
                    'INT': 'INTEGER',
                    'BIGINT': 'BIGINT',
                    'DECIMAL': 'DECIMAL(10,2)',
                    'NUMERIC': 'DECIMAL(10,2)',
                    'FLOAT': 'DOUBLE PRECISION',
                    'DOUBLE': 'DOUBLE PRECISION',
                    'BOOLEAN': 'BOOLEAN',
                    'BOOL': 'BOOLEAN',
                    'DATE': 'DATE',
                    'TIMESTAMP': 'TIMESTAMP',
                    'TIMESTAMPTZ': 'TIMESTAMP WITH TIME ZONE',
                    'TIME': 'TIME',
                    'JSON': 'JSONB',
                    'JSONB': 'JSONB'
                }
                pg_type = type_map.get(col_type.upper(), 'TEXT')

                col_def = f"    {col_name} {pg_type}"

                # Add description as comment if requested
                if include_comments and col_desc:
                    col_def += f"  -- {col_desc}"

                # Add example values if available and requested
                if include_examples and col.get('examples'):
                    examples = col['examples'][:3]  # First 3 examples
                    if not (include_comments and col_desc):
                        col_def += "  --"
                    col_def += f" Example: {', '.join(str(ex) for ex in examples)}"

                col_definitions.append(col_def)

            table_ddl += ",\n".join(col_definitions)

            # Primary key
            if primary_key:
                table_ddl += f",\n    PRIMARY KEY ({primary_key})"

            # Foreign keys
            for rel in relationships:
                if rel.get('joinType') in ['manyToOne', 'oneToOne']:
                    target_model = rel.get('targetModel', '')
                    join_keys = rel.get('joinKeys', {})

                    for local_key, foreign_key in join_keys.items():
                        table_ddl += f",\n    FOREIGN KEY ({local_key}) REFERENCES {target_model}({foreign_key})"

            table_ddl += "\n);"

            # Table comment
            if include_comments and description:
                table_ddl += f"\n-- Table description: {description}"

            ddl_parts.append(table_ddl)

        return "\n\n".join(ddl_parts)

    def to_markdown(self, include_metrics: bool = True) -> str:
        """
        Convert to Markdown format (light schema).

        Best for: LLM reasoning and understanding

        Args:
            include_metrics: Include available metrics

        Returns:
            Markdown-formatted schema string
        """
        md_parts = []

        # Header
        md_parts.append("# Database Schema\n")

        # Tables
        for model in self.models:
            table_name = model.get('name', 'unknown')
            description = model.get('description', 'No description')
            columns = model.get('columns', [])
            primary_key = model.get('primaryKey', '')
            relationships = model.get('relationships', [])

            # Table header
            md_parts.append(f"## Table: `{table_name}`")
            md_parts.append(f"{description}\n")

            # Columns
            md_parts.append("### Columns")
            md_parts.append("| Column | Type | Description | Examples |")
            md_parts.append("|--------|------|-------------|----------|")

            for col in columns:
                col_name = col.get('name', '')
                col_type = col.get('type', 'text')
                col_desc = col.get('description', '-')

                # Examples
                examples = col.get('examples', [])
                if examples:
                    example_str = ', '.join([f"`{ex}`" for ex in examples[:3]])
                else:
                    example_str = '-'

                # Clean description for table display
                col_desc_clean = col_desc.replace('|', '\\|').replace('\n', ' ')

                md_parts.append(f"| `{col_name}` | {col_type} | {col_desc_clean} | {example_str} |")

            # Primary key
            if primary_key:
                md_parts.append(f"\n**Primary Key:** `{primary_key}`")

            # Relationships
            if relationships:
                md_parts.append("\n### Relationships")
                for rel in relationships:
                    rel_name = rel.get('name', 'unknown')
                    join_type = rel.get('joinType', 'unknown')
                    target = rel.get('targetModel', 'unknown')
                    join_keys = rel.get('joinKeys', {})

                    join_desc = ', '.join([f"`{k}` = `{target}.{v}`" for k, v in join_keys.items()])
                    md_parts.append(f"- **{rel_name}** ({join_type}): {join_desc}")

            md_parts.append("")  # Spacing

        # Metrics
        if include_metrics and self.metrics:
            md_parts.append("## Available Metrics\n")

            for metric in self.metrics:
                metric_name = metric.get('name', 'unknown')
                metric_desc = metric.get('description', 'No description')
                base_obj = metric.get('baseObject', '-')
                aliases = metric.get('aliases', [])

                md_parts.append(f"### `{metric_name}`")
                md_parts.append(f"{metric_desc}")
                md_parts.append(f"- **Base Object:** `{base_obj}`")

                if aliases:
                    alias_str = ', '.join([f"`{a}`" for a in aliases])
                    md_parts.append(f"- **Aliases:** {alias_str}")

                md_parts.append("")

        return "\n".join(md_parts)

    def to_compact(self) -> str:
        """
        Convert to compact format for token efficiency.

        Best for: Minimizing prompt tokens while preserving essential info

        Returns:
            Compact schema string
        """
        lines = []

        for model in self.models:
            table = model.get('name', '')
            cols = [f"{c.get('name')}:{c.get('type', 'text')}" for c in model.get('columns', [])]
            lines.append(f"{table}({', '.join(cols)})")

        return "\n".join(lines)

    def get_table_summary(self, table_name: str) -> str:
        """
        Get detailed summary of a specific table.

        Args:
            table_name: Name of table

        Returns:
            Detailed table summary
        """
        for model in self.models:
            if model.get('name', '').lower() == table_name.lower():
                return self._to_markdown_single_table(model)

        return f"Table `{table_name}` not found in schema."

    def _to_markdown_single_table(self, model: Dict) -> str:
        """Get markdown for single table."""
        table_name = model.get('name', 'unknown')
        description = model.get('description', 'No description')
        columns = model.get('columns', [])

        md = f"## Table: `{table_name}`\n{description}\n\n"
        md += "| Column | Type | Description |\n"
        md += "|--------|------|-------------|\n"

        for col in columns:
            col_name = col.get('name', '')
            col_type = col.get('type', 'text')
            col_desc = col.get('description', '-').replace('|', '\\|').replace('\n', ' ')
            md += f"| `{col_name}` | {col_type} | {col_desc} |\n"

        return md

    def get_table_list(self) -> List[str]:
        """Get list of all table names."""
        return [model.get('name', '') for model in self.models if model.get('name')]

    def get_column_list(self, table_name: str) -> List[str]:
        """
        Get list of column names for a table.

        Args:
            table_name: Name of table

        Returns:
            List of column names
        """
        for model in self.models:
            if model.get('name', '').lower() == table_name.lower():
                return [col.get('name', '') for col in model.get('columns', []) if col.get('name')]

        return []

    def get_relationships(self, table_name: Optional[str] = None) -> List[Dict]:
        """
        Get relationships, optionally filtered by table.

        Args:
            table_name: Optional table name to filter by

        Returns:
            List of relationship definitions
        """
        relationships = []

        for model in self.models:
            if table_name and model.get('name', '').lower() != table_name.lower():
                continue

            model_relationships = model.get('relationships', [])
            for rel in model_relationships:
                relationships.append({
                    'source_table': model.get('name'),
                    'target_table': rel.get('targetModel'),
                    'join_type': rel.get('joinType'),
                    'join_keys': rel.get('joinKeys', {}),
                    'name': rel.get('name')
                })

        return relationships

    def validate_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the schema."""
        return any(
            model.get('name', '').lower() == table_name.lower()
            for model in self.models
        )

    def validate_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        for model in self.models:
            if model.get('name', '').lower() == table_name.lower():
                return any(
                    col.get('name', '').lower() == column_name.lower()
                    for col in model.get('columns', [])
                )
        return False
