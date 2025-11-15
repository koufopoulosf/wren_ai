"""
User Authorization

Simplified authorization for internal data engineer tool:
- Basic user role management (admin check)
- No department-based filtering (all users see all data)
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RowLevelSecurity:
    """
    Basic user authorization (no data filtering).

    Simplified for internal data engineer use - all authorized users
    have full data access.
    """

    def __init__(
        self,
        user_roles: Dict[str, Dict[str, str]],
        dept_access: Optional[Dict] = None  # Ignored, kept for compatibility
    ):
        """
        Initialize with user role mappings.

        Args:
            user_roles: Dict mapping Slack user IDs to role info
                {'U01ABC': {'role': 'admin'}}
            dept_access: Ignored (kept for backward compatibility)
        """
        self.user_roles = user_roles

        logger.info(f"✅ User authorization initialized with {len(user_roles)} users")
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        Get user's role info.

        Args:
            user_id: Slack user ID

        Returns:
            Dict with 'role' or None if user not found
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

    def apply_filter(self, sql: str, user_id: str) -> str:
        """
        Verify user authorization (no SQL modification for internal tool).

        Args:
            sql: Original SQL query
            user_id: Slack user ID

        Returns:
            Unmodified SQL (all users see all data)

        Raises:
            Exception: If user is not authorized
        """
        # Check authorization
        if not self.is_authorized(user_id):
            logger.warning(f"⚠️  Unauthorized access attempt: {user_id}")
            raise Exception(
                "🚫 You are not authorized to use this bot. "
                "Please contact your administrator for access."
            )

        logger.info(f"✅ User {user_id} authorized - full data access")
        return sql

    def is_admin(self, user_id: str) -> bool:
        """
        Check if user has admin role.

        Args:
            user_id: Slack user ID

        Returns:
            True if user is admin
        """
        user_info = self.get_user_info(user_id)
        return user_info and user_info.get("role") == "admin"