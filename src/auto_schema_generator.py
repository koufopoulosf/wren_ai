"""
Auto Schema Generator for PostgreSQL

Automatically profiles your PostgreSQL database and generates
semantic descriptions using Claude.

Security: Runs on your server, only metadata sent to Claude.

Usage in Streamlit:
    generator = AutoSchemaGenerator(db_config, anthropic_client)
    generator.connect()
    schema = generator.generate_schema()
    generator.save_to_file(schema, "database/mdl/schema.json")
    generator.disconnect()
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
from typing import Dict, List, Any
import logging
import asyncio
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AutoSchemaGenerator:
    """
    Automatically generates schema with descriptions from your PostgreSQL database.

    Integration with your existing project:
    - Uses your existing DB_CONFIG from config.py
    - Uses your existing ANTHROPIC_API_KEY
    - Generates MDL-compatible format
    - Can be triggered from Streamlit UI
    """

    # Columns to NEVER sample (PII/sensitive)
    SENSITIVE_PATTERNS = [
        'email', 'mail', 'phone', 'mobile', 'tel',
        'name', 'first_name', 'last_name', 'full_name',
        'ssn', 'social_security', 'passport', 'license',
        'address', 'street', 'city', 'zip', 'postal',
        'ip_address', 'credit_card', 'account_number',
        'password', 'pwd', 'secret', 'token', 'api_key',
        'dob', 'birth', 'age', 'salary', 'income'
    ]

    def __init__(self, db_config: Dict, anthropic_client: Anthropic, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize with your existing configuration.

        Args:
            db_config: Your database configuration from config.py
            anthropic_client: Your existing Anthropic client
            model: Claude model to use
        """
        self.db_config = db_config
        self.anthropic = anthropic_client
        self.model = model
        self.conn = None
        logger.info("🔧 AutoSchemaGenerator initialized")

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config.get('host', 'postgres'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'analytics'),
                user=self.db_config.get('user', 'wren_user'),
                password=self.db_config.get('password', 'wren_password'),
                sslmode='require' if self.db_config.get('ssl', False) else 'prefer'
            )
            logger.info("✅ Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Database connection closed")

    async def generate_schema(self, include_samples: bool = True, progress_callback=None) -> Dict:
        """
        Main method: Generate complete schema with AI descriptions.

        This is what you'll call from your Streamlit button.

        Args:
            include_samples: Include sample values for safe columns
            progress_callback: Optional callback for progress updates (text, percent)

        Returns:
            Complete schema dict compatible with your existing MDL format
        """
        logger.info("🔍 Starting automatic schema generation...")

        def update_progress(text: str, percent: int):
            if progress_callback:
                progress_callback(text, percent)

        # Step 1: Gather metadata from database
        update_progress("Profiling database tables...", 20)
        metadata = self._gather_metadata(include_samples)

        # Step 2: Generate descriptions using Claude
        update_progress("Generating AI descriptions...", 60)
        descriptions = await self._generate_descriptions(metadata)

        # Step 3: Convert to your existing MDL format
        update_progress("Converting to MDL format...", 90)
        mdl_schema = self._convert_to_mdl_format(metadata, descriptions)

        update_progress("Complete!", 100)
        logger.info("✅ Schema generation complete!")
        return mdl_schema

    def _gather_metadata(self, include_samples: bool) -> Dict:
        """
        Gather metadata from PostgreSQL.

        What we collect:
        - Table names and row counts
        - Column names, types, nullability
        - Distinct value counts
        - Min/max for dates and numbers
        - Sample values for low-cardinality columns (if safe)
        """
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "database_type": "postgresql",
            "tables": {}
        }

        # Get all tables
        tables = self._get_tables()
        logger.info(f"Found {len(tables)} tables")

        for table_name in tables:
            logger.info(f"  Profiling: {table_name}")

            table_meta = {
                "row_count": self._get_row_count(table_name),
                "columns": self._get_column_metadata(table_name, include_samples)
            }

            metadata["tables"][table_name] = table_meta

        return metadata

    def _get_tables(self) -> List[str]:
        """Get all tables in public schema"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables

    def _get_row_count(self, table_name: str) -> int:
        """Get total row count for table"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    def _get_column_metadata(self, table_name: str, include_samples: bool) -> Dict:
        """Get metadata for all columns in table"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get column info
        cursor.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))

        columns_info = cursor.fetchall()
        columns_metadata = {}

        for col_info in columns_info:
            col_name = col_info['column_name']

            col_metadata = {
                "data_type": col_info['data_type'],
                "nullable": col_info['is_nullable'] == 'YES',
            }

            # Get statistics
            stats = self._get_column_stats(table_name, col_name, col_info['data_type'])
            col_metadata.update(stats)

            # Get sample values for safe, low-cardinality columns
            if include_samples and self._is_safe_column(col_name):
                samples = self._get_sample_values(table_name, col_name, stats['distinct_count'])
                if samples:
                    col_metadata['sample_values'] = samples

            columns_metadata[col_name] = col_metadata

        cursor.close()
        return columns_metadata

    def _get_column_stats(self, table_name: str, col_name: str, data_type: str) -> Dict:
        """Get statistics for a column"""
        cursor = self.conn.cursor()
        stats = {}

        try:
            # NULL count
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE "{col_name}" IS NULL
            """)
            stats['null_count'] = cursor.fetchone()[0]

            # Distinct count
            cursor.execute(f"""
                SELECT COUNT(DISTINCT "{col_name}")
                FROM {table_name}
            """)
            stats['distinct_count'] = cursor.fetchone()[0]

            # Min/Max for numeric and date types
            if data_type in ['integer', 'bigint', 'numeric', 'real', 'double precision',
                            'date', 'timestamp', 'timestamp without time zone', 'timestamp with time zone']:
                try:
                    cursor.execute(f"""
                        SELECT MIN("{col_name}"), MAX("{col_name}")
                        FROM {table_name}
                        WHERE "{col_name}" IS NOT NULL
                    """)
                    result = cursor.fetchone()
                    if result:
                        min_val, max_val = result
                        if min_val is not None:
                            stats['min_value'] = str(min_val)
                        if max_val is not None:
                            stats['max_value'] = str(max_val)
                except Exception as e:
                    logger.debug(f"Could not get min/max for {col_name}: {e}")

        except Exception as e:
            logger.debug(f"Failed to get stats for {table_name}.{col_name}: {e}")

        cursor.close()
        return stats

    def _is_safe_column(self, col_name: str) -> bool:
        """
        Check if column is safe to sample (no PII).

        We NEVER sample PII or sensitive data.
        """
        col_lower = col_name.lower()
        return not any(pattern in col_lower for pattern in self.SENSITIVE_PATTERNS)

    def _get_sample_values(self, table_name: str, col_name: str, distinct_count: int) -> List[str]:
        """Get sample values for low-cardinality columns"""
        # Only sample if < 20 distinct values (probably enum/category)
        if distinct_count > 20:
            return []

        cursor = self.conn.cursor()

        try:
            cursor.execute(f"""
                SELECT "{col_name}", COUNT(*) as freq
                FROM {table_name}
                WHERE "{col_name}" IS NOT NULL
                GROUP BY "{col_name}"
                ORDER BY freq DESC
                LIMIT 5
            """)

            samples = [str(row[0]) for row in cursor.fetchall()]
        except Exception as e:
            logger.debug(f"Could not get samples for {col_name}: {e}")
            samples = []

        cursor.close()
        return samples

    async def _generate_descriptions(self, metadata: Dict) -> Dict:
        """
        Use Claude to generate descriptions from metadata.

        This sends ONLY metadata to Claude (no actual data).
        """
        logger.info("🤖 Generating descriptions with Claude...")

        prompt = self._build_description_prompt(metadata)

        try:
            # Call Claude API (async using executor)
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=6000,
                    temperature=0.3,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            )

            response_text = message.content[0].text

            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                descriptions = json.loads(json_match.group())
                logger.info("✅ Descriptions generated successfully")
                return descriptions
            else:
                logger.error("Failed to parse Claude's response")
                return self._generate_basic_descriptions(metadata)

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return self._generate_basic_descriptions(metadata)

    def _build_description_prompt(self, metadata: Dict) -> str:
        """Build prompt for Claude"""
        lines = [
            "You are a database documentation expert. Generate clear, business-focused descriptions.",
            "",
            "# PostgreSQL Database Metadata",
            ""
        ]

        for table_name, table_info in metadata['tables'].items():
            lines.append(f"## Table: {table_name}")
            lines.append(f"Rows: {table_info['row_count']:,}")
            lines.append("")

            for col_name, col_info in table_info['columns'].items():
                col_line = f"  - {col_name} ({col_info['data_type']})"
                col_line += f" | {col_info.get('distinct_count', 0):,} distinct"

                if col_info.get('null_count', 0) > 0:
                    null_pct = (col_info['null_count'] / table_info['row_count']) * 100
                    col_line += f", {null_pct:.1f}% null"

                if col_info.get('min_value'):
                    col_line += f" | range: {col_info['min_value']} to {col_info['max_value']}"

                if col_info.get('sample_values'):
                    samples = ', '.join(str(v) for v in col_info['sample_values'][:3])
                    col_line += f" | values: [{samples}]"

                lines.append(col_line)

            lines.append("")

        lines.extend([
            "# Task",
            "",
            "Generate descriptions in this JSON format:",
            "{",
            '  "tables": {',
            '    "table_name": {',
            '      "description": "Clear business description (10-20 words)",',
            '      "columns": {',
            '        "column_name": "What this represents (5-15 words)"',
            '      }',
            '    }',
            '  },',
            '  "relationships": [',
            '    {',
            '      "from_table": "...", "from_column": "...",',
            '      "to_table": "...", "to_column": "...",',
            '      "type": "one_to_many|many_to_one"',
            '    }',
            '  ]',
            '}',
            "",
            "Guidelines:",
            "- Infer meaning from column names and statistics",
            "- Be concise and business-focused",
            "- Identify foreign key relationships from column names ending in _id",
            "- Use simple language"
        ])

        return "\n".join(lines)

    def _generate_basic_descriptions(self, metadata: Dict) -> Dict:
        """Fallback: Generate basic descriptions without Claude"""
        descriptions = {"tables": {}, "relationships": []}

        for table_name, table_info in metadata['tables'].items():
            descriptions["tables"][table_name] = {
                "description": f"Table {table_name} with {table_info['row_count']:,} rows",
                "columns": {}
            }

            for col_name, col_info in table_info['columns'].items():
                descriptions["tables"][table_name]["columns"][col_name] = \
                    f"{col_info['data_type']} column"

        return descriptions

    def _convert_to_mdl_format(self, metadata: Dict, descriptions: Dict) -> Dict:
        """
        Convert to your existing MDL format.

        This generates the SAME structure as your database/mdl/schema.json
        """
        mdl = {
            "models": [],
            "metrics": []
        }

        for table_name, table_info in metadata['tables'].items():
            model = {
                "name": table_name,
                "description": descriptions['tables'][table_name]['description'],
                "table": table_name,
                "primaryKey": self._detect_primary_key(table_name, table_info['columns']),
                "columns": []
            }

            # Add columns
            for col_name, col_info in table_info['columns'].items():
                column = {
                    "name": col_name,
                    "type": self._map_pg_type_to_mdl(col_info['data_type']),
                    "description": descriptions['tables'][table_name]['columns'].get(
                        col_name,
                        f"{col_info['data_type']} column"
                    )
                }
                model['columns'].append(column)

            # Add relationships (if detected)
            relationships = self._detect_relationships(table_name, table_info['columns'], metadata)
            if relationships:
                model['relationships'] = relationships

            mdl['models'].append(model)

        # Generate basic metrics
        mdl['metrics'] = self._generate_basic_metrics(metadata)

        return mdl

    def _detect_primary_key(self, table_name: str, columns: Dict) -> str:
        """Detect primary key (usually *_id with all distinct values)"""
        for col_name, col_info in columns.items():
            # If column is called 'id' or '<table>_id' and has all distinct values
            if (col_name == 'id' or col_name == f'{table_name}_id') and \
               col_info.get('null_count', 0) == 0 and \
               col_info.get('distinct_count', 0) > 0:
                return col_name

        # Fallback: first column ending in _id
        for col_name in columns.keys():
            if col_name.endswith('_id'):
                return col_name

        return "id"  # Default guess

    def _detect_relationships(self, table_name: str, columns: Dict, metadata: Dict) -> List[Dict]:
        """Detect foreign key relationships from column names"""
        relationships = []

        for col_name, col_info in columns.items():
            # If column ends with _id (except primary key)
            if col_name.endswith('_id') and col_name not in ['id', f'{table_name}_id']:
                # Try to find referenced table
                # e.g., customer_id -> customers
                possible_table = col_name[:-3]  # Remove '_id'

                # Try plural form
                if possible_table + 's' in metadata['tables']:
                    relationships.append({
                        "name": f"{table_name}_to_{possible_table}",
                        "joinType": "manyToOne",
                        "targetModel": possible_table + 's',
                        "joinKeys": {col_name: col_name}
                    })
                # Try exact match
                elif possible_table in metadata['tables']:
                    relationships.append({
                        "name": f"{table_name}_to_{possible_table}",
                        "joinType": "manyToOne",
                        "targetModel": possible_table,
                        "joinKeys": {col_name: col_name}
                    })

        return relationships

    def _map_pg_type_to_mdl(self, pg_type: str) -> str:
        """Map PostgreSQL types to MDL types"""
        type_mapping = {
            'integer': 'integer',
            'bigint': 'integer',
            'smallint': 'integer',
            'numeric': 'decimal',
            'real': 'decimal',
            'double precision': 'decimal',
            'character varying': 'string',
            'varchar': 'string',
            'text': 'string',
            'char': 'string',
            'date': 'date',
            'timestamp': 'timestamp',
            'timestamp without time zone': 'timestamp',
            'timestamp with time zone': 'timestamp',
            'boolean': 'boolean'
        }

        return type_mapping.get(pg_type.lower(), 'string')

    def _generate_basic_metrics(self, metadata: Dict) -> List[Dict]:
        """Generate some basic metrics automatically"""
        metrics = []

        # Look for common metric patterns
        for table_name, table_info in metadata['tables'].items():
            columns = table_info['columns']

            # If there's an 'amount' or 'total' column, create a sum metric
            for col_name in columns.keys():
                if any(keyword in col_name.lower() for keyword in ['amount', 'total', 'price', 'revenue']):
                    metrics.append({
                        "name": f"total_{col_name}",
                        "aliases": [f"{col_name}_sum", f"{table_name}_{col_name}"],
                        "description": f"Total {col_name} from {table_name}",
                        "baseObject": table_name,
                        "measure": {
                            "type": "sum",
                            "column": col_name
                        }
                    })

            # Create a row count metric for each table
            metrics.append({
                "name": f"{table_name}_count",
                "aliases": [f"number_of_{table_name}", f"{table_name}_total"],
                "description": f"Total number of records in {table_name}",
                "baseObject": table_name,
                "measure": {
                    "type": "count",
                    "column": "*"
                }
            })

        return metrics[:10]  # Limit to 10 basic metrics

    def save_to_file(self, schema: Dict, filepath: str):
        """Save generated schema to file"""
        with open(filepath, 'w') as f:
            json.dump(schema, f, indent=2)

        logger.info(f"✅ Schema saved to: {filepath}")
