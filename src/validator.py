"""
SQL Validator

Validates SQL queries for safety by blocking dangerous operations.
"""

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)


class SQLValidator:
    """
    Validates SQL queries for safety.
    
    Blocks dangerous operations like DROP, DELETE, INSERT, UPDATE.
    Detects SQL injection patterns.
    """
    
    # Keywords that should never appear in queries
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE',
        'TRUNCATE', 'ALTER', 'CREATE', 'REPLACE',
        'GRANT', 'REVOKE', 'EXEC', 'EXECUTE',
        'CALL', 'DECLARE', 'SET'
    ]
    
    # Suspicious patterns that might indicate SQL injection
    INJECTION_PATTERNS = [
        r';\s*DROP',
        r';\s*DELETE',
        r';\s*UPDATE',
        r';\s*INSERT',
        r'--\s*$',  # Comment at end
        r'/\*.*\*/',  # Block comments
        r'xp_cmdshell',  # SQL Server command execution
        r'INTO\s+OUTFILE',  # MySQL file writing
        r'INTO\s+DUMPFILE',
        r'LOAD_FILE',
        r'eval\s*\(',
        r'exec\s*\(',
    ]
    
    def __init__(self):
        """Initialize validator."""
        logger.info("✅ SQL validator initialized")
    
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
    
    def validate(self, sql: str) -> Tuple[bool, str]:
        """
        Validate SQL for safety.
        
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
        
        logger.info("✅ SQL validation passed")
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