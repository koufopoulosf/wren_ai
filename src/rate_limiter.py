"""
Rate Limiter

Per-user rate limiting to prevent spam and abuse.
"""

import logging
from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter per user.
    
    Prevents users from spamming /ask commands.
    """
    
    def __init__(
        self,
        max_requests: int = 10,
        window_minutes: int = 1
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Max requests per window (default 10)
            window_minutes: Time window in minutes (default 1)
        """
        self.max_requests = max_requests
        self.window = timedelta(minutes=window_minutes)
        
        # Track request timestamps per user
        self.user_requests: Dict[str, list] = defaultdict(list)
        
        logger.info(
            f"✅ Rate limiter initialized: "
            f"{max_requests} requests per {window_minutes} minute(s)"
        )
    
    def check_rate_limit(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user is within rate limit.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            (is_allowed, error_message)
            - is_allowed: True if request allowed
            - error_message: Empty if allowed, error message if denied
        """
        now = datetime.now()
        
        # Clean old requests outside window
        cutoff = now - self.window
        self.user_requests[user_id] = [
            ts for ts in self.user_requests[user_id]
            if ts > cutoff
        ]
        
        # Count requests in current window
        request_count = len(self.user_requests[user_id])
        
        if request_count >= self.max_requests:
            # Rate limit exceeded
            oldest_request = min(self.user_requests[user_id])
            retry_after = (oldest_request + self.window) - now
            retry_seconds = int(retry_after.total_seconds())
            
            logger.warning(
                f"⚠️ Rate limit exceeded: {user_id} "
                f"({request_count}/{self.max_requests} in {self.window})"
            )
            
            error_msg = (
                f"🚫 Rate limit exceeded!\n\n"
                f"You've made {request_count} requests in the last "
                f"{self.window.seconds // 60} minute(s).\n"
                f"Please wait {retry_seconds} seconds before trying again.\n\n"
                f"💡 Tip: Use more specific questions to get better results faster."
            )
            
            return False, error_msg
        
        # Allow request and record timestamp
        self.user_requests[user_id].append(now)
        
        logger.info(
            f"✅ Rate limit check passed: {user_id} "
            f"({request_count + 1}/{self.max_requests})"
        )
        
        return True, ""
    
    def reset_user(self, user_id: str):
        """
        Reset rate limit for a user.
        
        Args:
            user_id: Slack user ID
        """
        if user_id in self.user_requests:
            del self.user_requests[user_id]
            logger.info(f"🔄 Rate limit reset for {user_id}")
    
    def get_remaining(self, user_id: str) -> int:
        """
        Get remaining requests for user in current window.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            Number of remaining requests
        """
        now = datetime.now()
        cutoff = now - self.window
        
        # Clean old requests
        self.user_requests[user_id] = [
            ts for ts in self.user_requests[user_id]
            if ts > cutoff
        ]
        
        used = len(self.user_requests[user_id])
        remaining = max(0, self.max_requests - used)
        
        return remaining
    
    def cleanup_expired(self):
        """Remove all expired request histories."""
        now = datetime.now()
        cutoff = now - self.window
        
        users_to_remove = []
        
        for user_id, timestamps in self.user_requests.items():
            # Keep only recent timestamps
            self.user_requests[user_id] = [
                ts for ts in timestamps
                if ts > cutoff
            ]
            
            # Remove user if no recent requests
            if not self.user_requests[user_id]:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del self.user_requests[user_id]
        
        if users_to_remove:
            logger.info(f"🗑️ Cleaned up {len(users_to_remove)} inactive users")
    
    def get_stats(self) -> Dict:
        """
        Get rate limiter statistics.
        
        Returns:
            Dict with stats
        """
        total_requests = sum(
            len(timestamps)
            for timestamps in self.user_requests.values()
        )
        
        return {
            "active_users": len(self.user_requests),
            "total_recent_requests": total_requests,
            "max_requests_per_window": self.max_requests,
            "window_minutes": self.window.seconds // 60
        }