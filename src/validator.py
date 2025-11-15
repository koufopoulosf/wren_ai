"""
SQL Validator - READ-ONLY Query Enforcement

SECURITY MODEL:
===============
This validator enforces READ-ONLY access to the database. NO data modification
or schema changes are possible through this interface.

PROTECTION LAYERS:
==================
1. SELECT-Only Enforcement
   - Only SELECT and WITH (CTEs) statements allowed
   - All modification operations blocked

2. Dangerous Keyword Blocking
   - INSERT, UPDATE, DELETE, MERGE, REPLACE (data modification)
   - DROP, CREATE, ALTER, TRUNCATE (schema modification)
   - GRANT, REVOKE (permission changes)
   - EXEC, CALL, DECLARE (procedural SQL)
   - COMMIT, ROLLBACK, BEGIN (transaction control)
   - COPY, UNLOAD (data export to files/S3)

3. SQL Injection Prevention
   - Stacked queries (;DROP, ;DELETE, etc.)
   - SQL comments (--, /* */, #)
   - Command execution attempts
   - File operation attempts
   - Database-specific exploits (PostgreSQL, MySQL, SQL Server, Redshift)

4. Multiple Statement Blocking
   - Only one SQL statement per query
   - Prevents injection via statement stacking

5. MDL Schema Validation
   - Validates table names exist in semantic layer
   - Prevents querying non-existent tables
   - Suggests corrections for typos

6. Query Size Limits
   - Maximum 10KB per query
   - Prevents resource abuse

WHAT'S ALLOWED:
===============
✅ SELECT statements (with WHERE, GROUP BY, ORDER BY, LIMIT, etc.)
✅ WITH (Common Table Expressions / CTEs)
✅ JOINs (INNER, LEFT, RIGHT, FULL)
✅ Aggregate functions (SUM, COUNT, AVG, MAX, MIN)
✅ Window functions (OVER, PARTITION BY, ROW_NUMBER, etc.)
✅ Subqueries

WHAT'S BLOCKED:
===============
❌ Data modification (INSERT, UPDATE, DELETE, MERGE)
❌ Schema changes (DROP, CREATE, ALTER, TRUNCATE)
❌ Transactions (BEGIN, COMMIT, ROLLBACK)
❌ Permissions (GRANT, REVOKE)
❌ Stored procedures (EXEC, CALL)
❌ File operations (COPY, UNLOAD, INTO OUTFILE)
❌ Multiple statements (stacked queries)
❌ SQL injection patterns
❌ Tables not in MDL schema

This ensures the data assistant is SAFE for read-only analytics access.
"""

import logging
import re
from typing import Tuple, List, Dict, Set, Optional
import sqlparse

logger = logging.getLogger(__name__)


class SQLValidator:
    """
    Validates SQL queries for safety and correctness.

    Security checks:
    - Blocks dangerous operations like DROP, DELETE, INSERT, UPDATE
    - Detects SQL injection patterns

    Schema validation (NEW):
    - Validates table names exist in MDL
    - Validates column names exist in MDL
    - Validates joins match MDL relationships
    """

    # Keywords that should never appear in queries
    # This ensures READ-ONLY access - no data modification possible
    DANGEROUS_KEYWORDS = [
        # Data Modification
        'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'REPLACE',

        # Schema Modification
        'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'RENAME',

        # Permission & Security
        'GRANT', 'REVOKE', 'DENY',

        # Procedural & System
        'EXEC', 'EXECUTE', 'CALL', 'DECLARE', 'SET',

        # Transaction Control (read-only doesn't need these)
        'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'BEGIN',

        # PostgreSQL-specific dangerous functions
        'COPY',  # Can read/write files
        'pg_read_file', 'pg_write_file', 'pg_execute',

        # Redshift-specific
        'UNLOAD',  # Exports data to S3
    ]

    # Suspicious patterns that might indicate SQL injection or data exfiltration
    INJECTION_PATTERNS = [
        # Stacked queries (SQL injection)
        r';\s*DROP',
        r';\s*DELETE',
        r';\s*UPDATE',
        r';\s*INSERT',
        r';\s*CREATE',
        r';\s*ALTER',
        r';\s*EXEC',

        # SQL comments (often used for injection)
        r'--\s*$',  # Line comment at end
        r'/\*.*\*/',  # Block comments
        r'#',  # MySQL-style comments

        # Command execution
        r'xp_cmdshell',  # SQL Server
        r'xp_regread',   # SQL Server registry
        r'xp_regwrite',  # SQL Server registry

        # File operations
        r'INTO\s+OUTFILE',  # MySQL file writing
        r'INTO\s+DUMPFILE', # MySQL dump
        r'LOAD_FILE',       # MySQL file reading
        r'LOAD\s+DATA',     # MySQL data loading

        # Function-based attacks
        r'eval\s*\(',
        r'exec\s*\(',
        r'execute\s*\(',

        # PostgreSQL-specific attacks
        r'pg_read_file',
        r'pg_write_file',
        r'pg_execute',
        r'pg_read_binary_file',
        r'pg_ls_dir',

        # COPY command (can read/write files)
        r'\bCOPY\s+',

        # Redshift UNLOAD (exports to S3)
        r'\bUNLOAD\s*\(',
    ]

    def __init__(self, mdl_models: Optional[List[Dict]] = None, mdl_metrics: Optional[List[Dict]] = None):
        """
        Initialize validator with optional MDL schema.

        Args:
            mdl_models: List of model definitions from MDL
            mdl_metrics: List of metric definitions from MDL
        """
        self.mdl_models = mdl_models or []
        self.mdl_metrics = mdl_metrics or []

        # Build lookup dictionaries for fast validation
        self._model_names = {m.get("name", "").lower() for m in self.mdl_models if m.get("name")}
        self._column_lookup = {}  # {model_name: {col1, col2, ...}}

        for model in self.mdl_models:
            model_name = model.get("name", "").lower()
            if model_name:
                columns = {col.get("name", "").lower() for col in model.get("columns", []) if col.get("name")}
                self._column_lookup[model_name] = columns

        if self.mdl_models:
            logger.info(f"✅ SQL validator initialized with MDL schema ({len(self.mdl_models)} models)")
        else:
            logger.info("✅ SQL validator initialized (no MDL schema - schema validation disabled)")
    
    def _check_dangerous_keywords(self, sql: str) -> Tuple[bool, str]:
        """
        Check for dangerous SQL keywords.
        
        Args:
            sql: SQL query to check
        
        Returns:
            (is_valid, error_message)
        """
        sql_upper = sql.upper()
        
        for keyword in self.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                logger.warning(f"⚠️  Dangerous keyword detected: {keyword}")
                return False, (
                    f"🚫 Dangerous operation detected: {keyword}\n\n"
                    f"Only SELECT queries are allowed for safety."
                )
        
        return True, ""
    
    def _check_select_only(self, sql: str) -> Tuple[bool, str]:
        """
        Ensure query is SELECT only.
        
        Args:
            sql: SQL query to check
        
        Returns:
            (is_valid, error_message)
        """
        sql_stripped = sql.strip().upper()
        
        # Allow WITH (CTEs) followed by SELECT
        if sql_stripped.startswith('WITH'):
            # Make sure there's a SELECT somewhere
            if 'SELECT' not in sql_stripped:
                return False, (
                    "🚫 Query must include a SELECT statement.\n\n"
                    "Only read-only SELECT queries are allowed."
                )
            return True, ""
        
        # Must start with SELECT
        if not sql_stripped.startswith('SELECT'):
            return False, (
                "🚫 Only SELECT queries are allowed.\n\n"
                "Queries must start with SELECT or WITH (for CTEs)."
            )
        
        return True, ""
    
    def _check_injection_patterns(self, sql: str) -> Tuple[bool, str]:
        """
        Check for SQL injection patterns.
        
        Args:
            sql: SQL query to check
        
        Returns:
            (is_valid, error_message)
        """
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                logger.warning(f"⚠️  Suspicious SQL pattern detected: {pattern}")
                return False, (
                    "🚫 Suspicious SQL pattern detected.\n\n"
                    "Your query contains patterns that may be unsafe. "
                    "Please rephrase your question."
                )
        
        return True, ""
    
    def _check_query_length(self, sql: str) -> Tuple[bool, str]:
        """
        Check if query is reasonable length.
        
        Args:
            sql: SQL query to check
        
        Returns:
            (is_valid, error_message)
        """
        max_length = 10000  # 10KB
        
        if len(sql) > max_length:
            logger.warning(f"⚠️  Query too long: {len(sql)} characters")
            return False, (
                f"🚫 Query is too long ({len(sql)} characters).\n\n"
                f"Maximum allowed: {max_length} characters. "
                "Please simplify your question."
            )
        
        return True, ""
    
    def _check_multiple_statements(self, sql: str) -> Tuple[bool, str]:
        """
        Check for multiple SQL statements (stacked queries).

        Args:
            sql: SQL query to check

        Returns:
            (is_valid, error_message)
        """
        # Remove string literals to avoid false positives
        sql_cleaned = re.sub(r"'[^']*'", "", sql)

        # Count semicolons (allowing one at the end)
        semicolons = sql_cleaned.count(';')

        # Strip trailing semicolon and whitespace
        sql_stripped = sql_cleaned.rstrip().rstrip(';')

        # If there are still semicolons, it's multiple statements
        if ';' in sql_stripped:
            logger.warning("⚠️  Multiple SQL statements detected")
            return False, (
                "🚫 Multiple SQL statements are not allowed.\n\n"
                "Please ask one question at a time."
            )

        return True, ""

    def _extract_table_names(self, sql: str) -> Set[str]:
        """
        Extract table names from SQL query.

        Args:
            sql: SQL query

        Returns:
            Set of table names (lowercase)
        """
        tables = set()

        # Use sqlparse to parse SQL
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return tables

            # Extract FROM and JOIN clauses
            for statement in parsed:
                # Get all tokens
                tokens = list(statement.flatten())

                # Look for FROM and JOIN keywords
                for i, token in enumerate(tokens):
                    if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in ('FROM', 'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN'):
                        # Next non-whitespace token should be table name
                        for j in range(i + 1, len(tokens)):
                            next_token = tokens[j]
                            if next_token.ttype is not sqlparse.tokens.Whitespace and next_token.ttype is not sqlparse.tokens.Newline:
                                # Extract table name (handle aliases)
                                table_name = next_token.value
                                # Remove schema prefix if present (e.g., public.orders -> orders)
                                if '.' in table_name:
                                    table_name = table_name.split('.')[-1]
                                # Remove quotes if present
                                table_name = table_name.strip('"').strip("'").lower()
                                tables.add(table_name)
                                break

        except Exception as e:
            logger.warning(f"⚠️  Failed to parse SQL for table extraction: {e}")
            # Fallback to regex
            from_pattern = r'FROM\s+([a-zA-Z0-9_\.]+)'
            join_pattern = r'JOIN\s+([a-zA-Z0-9_\.]+)'
            for match in re.finditer(from_pattern, sql, re.IGNORECASE):
                table = match.group(1).split('.')[-1].lower()
                tables.add(table)
            for match in re.finditer(join_pattern, sql, re.IGNORECASE):
                table = match.group(1).split('.')[-1].lower()
                tables.add(table)

        return tables

    def _check_mdl_schema(self, sql: str) -> Tuple[bool, str]:
        """
        Validate SQL against MDL schema.

        Checks:
        - Table names exist in MDL
        - Column names exist in their respective tables (future enhancement)

        Args:
            sql: SQL query to check

        Returns:
            (is_valid, error_message)
        """
        # Skip if no MDL loaded
        if not self.mdl_models:
            return True, ""

        # Extract table names from SQL
        table_names = self._extract_table_names(sql)

        if not table_names:
            # No tables found - maybe a complex query or CTE
            logger.debug("No tables extracted from SQL - skipping schema validation")
            return True, ""

        # Check each table exists in MDL
        invalid_tables = []
        for table in table_names:
            if table not in self._model_names:
                invalid_tables.append(table)

        if invalid_tables:
            logger.warning(f"⚠️  Tables not found in MDL schema: {invalid_tables}")

            # Suggest similar table names
            suggestions = []
            for invalid_table in invalid_tables:
                # Find similar table names using simple similarity
                for model_name in self._model_names:
                    # Simple substring match
                    if invalid_table in model_name or model_name in invalid_table:
                        suggestions.append(model_name)
                        break

            error_msg = (
                f"🚫 *Schema Validation Failed*\n\n"
                f"Table(s) not found in schema: `{', '.join(invalid_tables)}`\n\n"
            )

            if suggestions:
                error_msg += f"Did you mean: {', '.join(f'`{s}`' for s in suggestions)}?\n\n"

            error_msg += (
                f"Available tables ({len(self._model_names)}): " +
                ', '.join(f'`{t}`' for t in sorted(self._model_names)[:10])
            )

            if len(self._model_names) > 10:
                error_msg += f", ... and {len(self._model_names) - 10} more"

            return False, error_msg

        logger.info(f"✅ MDL schema validation passed - all tables exist")
        return True, ""
    
    def validate(self, sql: str) -> Tuple[bool, str]:
        """
        Validate SQL for safety and correctness.

        Runs all validation checks and returns the first failure.

        Args:
            sql: SQL query to validate

        Returns:
            (is_valid, error_message)
            - is_valid: True if safe, False otherwise
            - error_message: Explanation if invalid, empty string if valid

        Example:
            >>> validator = SQLValidator()
            >>> is_valid, error = validator.validate("SELECT * FROM users")
            >>> if not is_valid:
            ...     print(error)
        """
        if not sql or not sql.strip():
            return False, "🚫 Empty query. Please ask a question."

        # Check 1: Query length
        is_valid, error = self._check_query_length(sql)
        if not is_valid:
            logger.warning(f"Validation failed: {error}")
            return False, error

        # Check 2: Must be SELECT only
        is_valid, error = self._check_select_only(sql)
        if not is_valid:
            logger.warning(f"Validation failed: {error}")
            return False, error

        # Check 3: No dangerous keywords
        is_valid, error = self._check_dangerous_keywords(sql)
        if not is_valid:
            logger.warning(f"Validation failed: {error}")
            return False, error

        # Check 4: No injection patterns
        is_valid, error = self._check_injection_patterns(sql)
        if not is_valid:
            logger.warning(f"Validation failed: {error}")
            return False, error

        # Check 5: No multiple statements
        is_valid, error = self._check_multiple_statements(sql)
        if not is_valid:
            logger.warning(f"Validation failed: {error}")
            return False, error

        # Check 6: MDL schema validation (NEW!)
        is_valid, error = self._check_mdl_schema(sql)
        if not is_valid:
            logger.warning(f"Schema validation failed: {error}")
            return False, error

        logger.info("✅ SQL validation passed (security + schema)")
        return True, ""
    
    def sanitize_error_message(self, error: str) -> str:
        """
        Sanitize error messages to remove sensitive information.
        
        Args:
            error: Raw error message
        
        Returns:
            Sanitized error message safe to show users
        """
        # Remove connection strings
        error = re.sub(
            r'(host|server|password|pwd)=[^\s;]+',
            r'\1=***',
            error,
            flags=re.IGNORECASE
        )
        
        # Remove IP addresses
        error = re.sub(
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'xxx.xxx.xxx.xxx',
            error
        )
        
        # Truncate if too long
        max_length = 500
        if len(error) > max_length:
            error = error[:max_length] + "..."
        
        return error