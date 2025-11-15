"""
LLM-Based Metadata Description Generator

Reads metadata file (from secure_profiler.py) and sends ONLY metadata to Claude.
No database connection, no credentials, no sensitive data.

Security:
- Never touches database
- Only reads metadata JSON
- Sends only statistics to Claude
- No PII exposure
"""

import json
import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class SecureLLMDescriptor:
    """
    Generates semantic descriptions from metadata.

    Security: This never touches your database.
    It only reads the metadata JSON file you created.
    """

    def __init__(self, anthropic_api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize with Anthropic API key.

        Args:
            anthropic_api_key: Your Anthropic API key
            model: Claude model to use
        """
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.model = model
        logger.info(f"✅ LLM descriptor initialized with {model}")

    def load_metadata(self, filepath: str) -> Dict:
        """
        Load metadata from file (no DB connection needed).

        Args:
            filepath: Path to metadata JSON file

        Returns:
            Metadata dictionary
        """
        with open(filepath, 'r') as f:
            metadata = json.load(f)

        logger.info(f"📂 Loaded metadata from: {filepath}")
        logger.info(f"   Tables: {len(metadata['tables'])}")
        logger.info(f"   Generated: {metadata.get('generated_at', 'unknown')}")

        return metadata

    async def generate_descriptions(self, metadata: Dict) -> Dict:
        """
        Send ONLY metadata to Claude.
        Get back semantic descriptions.

        Args:
            metadata: Database metadata (from secure_profiler)

        Returns:
            {
                "tables": {
                    "table_name": {
                        "description": "...",
                        "purpose": "...",
                        "columns": {
                            "col_name": {
                                "description": "...",
                                "business_meaning": "..."
                            }
                        }
                    }
                },
                "relationships": [...]
            }
        """
        metadata_size_kb = len(json.dumps(metadata)) / 1024

        logger.info("🤖 Sending metadata to Claude...")
        logger.info(f"   Data size: {metadata_size_kb:.1f} KB")
        logger.info(f"   (No sensitive data, only metadata)")

        prompt = self._build_prompt(metadata)

        try:
            # Call Claude API (async using executor)
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=8000,
                    temperature=0.3,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            )

            response_text = message.content[0].text

            # Parse JSON response
            descriptions = self._parse_response(response_text)

            logger.info("✅ Descriptions generated successfully")
            logger.info(f"   Tables described: {len(descriptions.get('tables', {}))}")

            return descriptions

        except Exception as e:
            logger.error(f"❌ Failed to generate descriptions: {e}", exc_info=True)
            raise

    def _build_prompt(self, metadata: Dict) -> str:
        """Build prompt with metadata only (no data)"""
        prompt_parts = [
            "You are a database documentation expert. Generate clear, business-focused descriptions.",
            "",
            "# Database Metadata (NO ACTUAL DATA)",
            "",
            f"Database: {metadata.get('database_name', 'unknown')}",
            f"Type: {metadata.get('database_type', 'unknown')}",
            f"Profiled: {metadata.get('generated_at', 'unknown')}",
            ""
        ]

        for table_name, table_info in metadata['tables'].items():
            prompt_parts.append(f"## Table: {table_name}")
            prompt_parts.append(f"Rows: {table_info['row_count']:,}")
            prompt_parts.append("")

            for col_name, col_info in table_info['columns'].items():
                col_line = f"  - {col_name} ({col_info['data_type']})"

                # Add statistics
                col_line += f" | {col_info.get('distinct_count', 0):,} distinct"

                if col_info.get('null_count', 0) > 0:
                    null_pct = (col_info['null_count'] / table_info['row_count']) * 100
                    col_line += f", {null_pct:.1f}% null"

                # Add nullability
                if col_info.get('nullable'):
                    col_line += ", nullable"

                # Add ranges if available
                if col_info.get('min_value') and col_info.get('max_value'):
                    col_line += f" | range: {col_info['min_value']} to {col_info['max_value']}"

                # Add sample values if available
                if col_info.get('sample_values'):
                    samples = ', '.join(str(v) for v in col_info['sample_values'])
                    col_line += f" | samples: [{samples}]"

                prompt_parts.append(col_line)

            prompt_parts.append("")

        prompt_parts.extend([
            "",
            "# Task",
            "",
            "Generate semantic descriptions in this JSON format:",
            "{",
            '  "tables": {',
            '    "table_name": {',
            '      "description": "Business-focused description (10-20 words)",',
            '      "purpose": "What this table is used for",',
            '      "columns": {',
            '        "column_name": {',
            '          "description": "What this column represents (5-15 words)",',
            '          "business_meaning": "How this is used in business context"',
            '        }',
            '      }',
            '    }',
            '  },',
            '  "relationships": [',
            '    {',
            '      "from_table": "...",',
            '      "from_column": "...",',
            '      "to_table": "...",',
            '      "to_column": "...",',
            '      "relationship_type": "one-to-many|many-to-one|many-to-many",',
            '      "description": "..."',
            '    }',
            '  ]',
            '}',
            "",
            "Guidelines:",
            "- Infer semantics from column names and statistics",
            "- Be concise and business-focused",
            "- Identify likely foreign key relationships (look for _id columns)",
            "- Note data quality issues (high nulls, etc.)",
            "- Use simple, clear language",
            "- Infer relationships from column names (customer_id → customers table)",
            "- Sample values provide hints about categorical data"
        ])

        return "\n".join(prompt_parts)

    def _parse_response(self, response_text: str) -> Dict:
        """Parse Claude's JSON response"""
        import re

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                logger.debug(f"Response: {response_text[:500]}")
                raise

        raise ValueError("No valid JSON found in Claude's response")

    def save_descriptions(self, descriptions: Dict, output_dir: str = "metadata") -> str:
        """
        Save generated descriptions.

        Returns:
            Path to saved file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        from datetime import datetime
        filename = f"db_descriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = output_path / filename

        with open(filepath, 'w') as f:
            json.dump(descriptions, f, indent=2)

        logger.info(f"✅ Descriptions saved to: {filepath}")
        return str(filepath)

    def format_for_wren(self, descriptions: Dict) -> str:
        """
        Format descriptions as natural language schema for Wren AI.

        Returns:
            Schema text to include in prompts
        """
        lines = ["# Database Schema with AI-Generated Descriptions", "", ""]

        for table_name, table_info in descriptions.get('tables', {}).items():
            lines.append(f"## {table_name}")
            lines.append(f"**Description:** {table_info.get('description', 'N/A')}")
            lines.append(f"**Purpose:** {table_info.get('purpose', 'N/A')}")
            lines.append("")
            lines.append("**Columns:**")

            for col_name, col_info in table_info.get('columns', {}).items():
                lines.append(f"  - `{col_name}`: {col_info.get('description', 'N/A')}")
                if col_info.get('business_meaning'):
                    lines.append(f"    *{col_info['business_meaning']}*")

            lines.append("")

        # Add relationships
        if descriptions.get('relationships'):
            lines.append("## Relationships")
            lines.append("")

            for rel in descriptions['relationships']:
                lines.append(
                    f"  - `{rel.get('from_table', '?')}.{rel.get('from_column', '?')}` → "
                    f"`{rel.get('to_table', '?')}.{rel.get('to_column', '?')}` "
                    f"({rel.get('relationship_type', 'unknown')})"
                )
                if rel.get('description'):
                    lines.append(f"    {rel['description']}")
                lines.append("")

        return "\n".join(lines)

    def save_wren_schema(self, descriptions: Dict, output_dir: str = "metadata") -> str:
        """
        Save schema formatted for Wren AI.

        Returns:
            Path to saved file
        """
        schema_text = self.format_for_wren(descriptions)

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        from datetime import datetime
        filename = f"schema_for_wren_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = output_path / filename

        with open(filepath, 'w') as f:
            f.write(schema_text)

        logger.info(f"✅ Wren schema saved to: {filepath}")
        return str(filepath)


async def main():
    """
    Run this AFTER you've run secure_profiler.py
    """
    import sys

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Get metadata file path
    if len(sys.argv) > 1:
        metadata_file = sys.argv[1]
    else:
        # Find most recent metadata file
        metadata_dir = Path("metadata")
        if not metadata_dir.exists():
            print("❌ Error: No metadata directory found. Run secure_profiler.py first.")
            sys.exit(1)

        metadata_files = list(metadata_dir.glob("db_metadata_*.json"))
        if not metadata_files:
            print("❌ Error: No metadata files found. Run secure_profiler.py first.")
            sys.exit(1)

        metadata_file = str(sorted(metadata_files)[-1])
        print(f"📂 Using most recent metadata file: {metadata_file}")

    descriptor = SecureLLMDescriptor(anthropic_api_key=api_key)

    # Load metadata (no DB connection)
    print("\n📂 Loading metadata...")
    metadata = descriptor.load_metadata(metadata_file)

    # Generate descriptions with Claude
    print("\n🤖 Generating descriptions with Claude...")
    descriptions = await descriptor.generate_descriptions(metadata)

    # Save descriptions
    print("\n💾 Saving outputs...")
    desc_file = descriptor.save_descriptions(descriptions)
    schema_file = descriptor.save_wren_schema(descriptions)

    print("\n✅ Complete! Generated files:")
    print(f"   • {desc_file} (structured JSON)")
    print(f"   • {schema_file} (formatted for Wren AI)")
    print("\n📤 Next step: Use these descriptions with your Wren AI client")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
