"""
Row-Level Security (RLS)

Implements department-based data access control by:
- Injecting WHERE clause filters into SQL
- Managing user roles and permissions
- Providing security explanations to users
"""

import logging
from typing import Dict, Optional, List
import sqlparse
from sqlparse.sql import Where, Token, Identifier, Comparison
from sqlparse.tokens import Keyword, Whitespace

logger = logging.getLogger(__name__)


class RowLevelSecurity:
    """
    Applies row-level security filters to SQL queries.
    
    Automatically injects department-based WHERE clauses to ensure
    users only see data they're authorized to access.
    """
    
    def __init__(
        self, 
        user_roles: Dict[str, Dict[str, str]],
        dept_access: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize RLS with user role mappings.
        
        Args:
            user_roles: Dict mapping Slack user IDs to role info
                {
                    'U01ABC': {'role': 'admin', 'department': 'all'},
                    'U02DEF': {'role': 'analyst', 'department': 'sales'}
                }
            dept_access: Optional dict mapping departments to allowed tables
        """
        self.user_roles = user_roles
        self.dept_access = dept_access or {}
        
        logger.info(f"✅ RLS initialized with {len(user_roles)} user mappings")
        logger.info(f"✅ Department access rules: {len(self.dept_access)} departments")
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        Get user's role and department.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            Dict with 'role' and 'department' or None if user not found
        """
        return self.user_roles.get(user_id)
    
    def is_authorized(self, user_id: str) -> bool:
        """
        Check if user is authorized to use the bot.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            True if user is in USER_ROLES configuration
        """
        return user_id in self.user_roles
    
    def _needs_filter(self, user_id: str) -> bool:
        """
        Check if user needs department filter applied.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            True if filter should be applied, False for admins
        """
        user_info = self.get_user_info(user_id)
        
        if not user_info:
            return True  # Unknown users get filtered (safe default)
        
        # Admins and users with 'all' department don't need filters
        role = user_info.get("role", "")
        department = user_info.get("department", "")
        
        return role != "admin" and department != "all"
    
    def _build_filter_clause(self, department: str) -> str:
        """
        Build SQL filter clause for department.
        
        Args:
            department: Department name (e.g., 'sales', 'marketing')
        
        Returns:
            SQL filter string (e.g., "department = 'sales'")
        """
        # Escape single quotes to prevent SQL injection
        safe_dept = department.replace("'", "''")
        return f"department = '{safe_dept}'"
    
    def _inject_filter_simple(self, sql: str, filter_clause: str) -> str:
        """
        Simple filter injection for basic SELECT statements.
        
        Handles:
        - SELECT ... FROM table
        - SELECT ... FROM table WHERE ...
        - SELECT with ORDER BY, GROUP BY, LIMIT
        
        Args:
            sql: Original SQL
            filter_clause: Filter to inject
        
        Returns:
            Modified SQL with filter
        """
        sql_upper = sql.upper()
        
        # Find WHERE clause
        where_idx = sql_upper.find(" WHERE ")
        
        if where_idx > 0:
            # Append to existing WHERE with AND
            # Find the end of WHERE clause
            end_keywords = [
                " ORDER BY ", " GROUP BY ", " HAVING ",
                " LIMIT ", " OFFSET ", ";"
            ]
            end_idx = len(sql)
            
            for keyword in end_keywords:
                idx = sql_upper.find(keyword, where_idx)
                if idx > 0 and idx < end_idx:
                    end_idx = idx
            
            # Insert filter before the end
            modified = (
                sql[:end_idx] +
                f" AND {filter_clause}" +
                sql[end_idx:]
            )
            
            logger.info(f"✅ Appended RLS filter to existing WHERE clause")
        else:
            # No WHERE clause - add one
            # Find insertion point (before ORDER BY, GROUP BY, etc.)
            end_keywords = [
                " ORDER BY ", " GROUP BY ", " HAVING ",
                " LIMIT ", " OFFSET ", ";"
            ]
            insert_idx = len(sql)
            
            for keyword in end_keywords:
                idx = sql_upper.find(keyword)
                if idx > 0 and idx < insert_idx:
                    insert_idx = idx
            
            # Insert WHERE clause
            modified = (
                sql[:insert_idx] +
                f" WHERE {filter_clause}" +
                sql[insert_idx:]
            )
            
            logger.info(f"✅ Added new WHERE clause with RLS filter")
        
        return modified
    
    def apply_filter(self, sql: str, user_id: str) -> str:
        """
        Apply RLS filter to SQL query.
        
        Args:
            sql: Original SQL query
            user_id: Slack user ID
        
        Returns:
            Modified SQL with department filter (if applicable)
        
        Raises:
            Exception: If user is not authorized or SQL is invalid
        """
        # Get user info
        user_info = self.get_user_info(user_id)
        
        if not user_info:
            logger.warning(f"⚠️  Unauthorized access attempt: {user_id}")
            raise Exception(
                "🚫 You are not authorized to run queries. "
                "Please contact your administrator for access."
            )
        
        role = user_info.get("role", "")
        department = user_info.get("department", "")
        
        # Log access attempt
        logger.info(
            f"RLS check: user={user_id}, role={role}, dept={department}"
        )
        
        # Check if filter is needed
        if not self._needs_filter(user_id):
            logger.info(f"✅ No RLS filter needed for {role} user")
            return sql
        
        # Build and apply filter
        filter_clause = self._build_filter_clause(department)
        
        try:
            modified_sql = self._inject_filter_simple(sql, filter_clause)
            
            logger.info(
                f"✅ Applied RLS filter for department: {department}"
            )
            logger.debug(f"Original SQL: {sql[:200]}")
            logger.debug(f"Modified SQL: {modified_sql[:200]}")
            
            return modified_sql
        
        except Exception as e:
            logger.error(f"❌ Failed to apply RLS filter: {e}", exc_info=True)
            raise Exception(
                "Failed to apply security filter. "
                "Please contact your administrator."
            )
    
    def explain_filter(self, user_id: str) -> str:
        """
        Generate human-readable explanation of applied filter.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            Explanation string for display to user
        """
        user_info = self.get_user_info(user_id)
        
        if not user_info:
            return "⚠️ User not authorized"
        
        role = user_info.get("role", "")
        department = user_info.get("department", "")
        
        if not self._needs_filter(user_id):
            return "🔓 No data filters (admin access)"
        
        return f"🔒 Data filtered to: {department} department"
    
    def validate_table_access(
        self, 
        user_id: str, 
        table_name: str
    ) -> bool:
        """
        Check if user has access to a specific table.
        
        Args:
            user_id: Slack user ID
            table_name: Table name (e.g., 'public.orders')
        
        Returns:
            True if user can access table
        """
        user_info = self.get_user_info(user_id)
        
        if not user_info:
            return False
        
        role = user_info.get("role", "")
        department = user_info.get("department", "")
        
        # Admins can access everything
        if role == "admin" or department == "all":
            return True
        
        # Check department-specific access
        allowed_tables = self.dept_access.get(department, [])
        
        # If no specific rules, allow all tables (filter via WHERE clause)
        if not allowed_tables:
            return True
        
        # Check if table matches any allowed patterns
        for allowed in allowed_tables:
            # Support wildcard: public.*
            if allowed.endswith(".*"):
                schema = allowed.split(".")[0]
                if table_name.startswith(f"{schema}."):
                    return True
            # Exact match
            elif allowed == table_name:
                return True
        
        logger.warning(
            f"⚠️  Table access denied: user={user_id}, "
            f"dept={department}, table={table_name}"
        )
        
        return False
    
    def get_accessible_tables(self, user_id: str) -> Optional[List[str]]:
        """
        Get list of tables accessible by user.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            List of table names, or None for admin (all tables)
        """
        user_info = self.get_user_info(user_id)
        
        if not user_info:
            return []
        
        role = user_info.get("role", "")
        department = user_info.get("department", "")
        
        # Admins get all tables
        if role == "admin" or department == "all":
            return None
        
        # Return department-specific tables
        return self.dept_access.get(department, [])