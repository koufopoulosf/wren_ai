"""
Configuration Module

Manages all environment variables, logging setup, and application configuration.
Includes comprehensive logging for audit trails and monitoring.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()


class Config:
    """
    Central configuration manager for the Wren AI Slack Bot.
    
    Handles:
    - Environment variable loading and validation
    - User role management
    - Department access control
    - Logging configuration
    - Claude/Anthropic client initialization
    """
    
    def __init__(self):
        """Initialize configuration and set up logging."""
        # Wren AI Configuration
        self.WREN_URL = os.getenv("WREN_URL", "http://wren-ai:8000")
        self.WREN_PROJECT_ID = os.getenv("WREN_PROJECT_ID", "analytics")
        
        # Anthropic/Claude Configuration
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        # Using Claude Sonnet 4.5 (latest model)
        self.ANTHROPIC_MODEL = os.getenv(
            "ANTHROPIC_MODEL", 
            "claude-sonnet-4-20250514"
        )
        
        # Slack Configuration
        self.SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
        self.SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
        self.SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
        
        if not all([self.SLACK_BOT_TOKEN, self.SLACK_APP_TOKEN]):
            raise ValueError("SLACK_BOT_TOKEN and SLACK_APP_TOKEN are required")
        
        # AWS Redshift Configuration
        self.REDSHIFT_HOST = os.getenv("REDSHIFT_HOST")
        self.REDSHIFT_PORT = int(os.getenv("REDSHIFT_PORT", "5439"))
        self.REDSHIFT_DATABASE = os.getenv("REDSHIFT_DATABASE")
        self.REDSHIFT_USER = os.getenv("REDSHIFT_USER")
        self.REDSHIFT_PASSWORD = os.getenv("REDSHIFT_PASSWORD")
        self.DB_SSL = os.getenv("DB_SSL", "true").lower() == "true"
        
        # Safety Limits
        self.MAX_QUERY_TIMEOUT_SECONDS = int(
            os.getenv("MAX_QUERY_TIMEOUT_SECONDS", "30")
        )
        self.MAX_ROWS_DISPLAY = int(os.getenv("MAX_ROWS_DISPLAY", "50"))
        self.MAX_ROWS_EXPORT = int(os.getenv("MAX_ROWS_EXPORT", "10000"))
        
        # Export Settings
        self.ENABLE_CSV_EXPORT = os.getenv("ENABLE_CSV_EXPORT", "true").lower() == "true"
        self.ENABLE_JSON_EXPORT = os.getenv("ENABLE_JSON_EXPORT", "true").lower() == "true"
        self.ENABLE_CHARTS = os.getenv("ENABLE_CHARTS", "true").lower() == "true"
        
        # Advanced Features
        self.ENABLE_PROGRESSIVE_CLARIFICATION = os.getenv(
            "ENABLE_PROGRESSIVE_CLARIFICATION", "true"
        ).lower() == "true"
        self.ENABLE_ALTERNATIVE_SUGGESTIONS = os.getenv(
            "ENABLE_ALTERNATIVE_SUGGESTIONS", "true"
        ).lower() == "true"
        
        # Confidence Thresholds
        self.CONFIDENCE_THRESHOLD_HIGH = float(
            os.getenv("CONFIDENCE_THRESHOLD_HIGH", "0.85")
        )
        self.CONFIDENCE_THRESHOLD_LOW = float(
            os.getenv("CONFIDENCE_THRESHOLD_LOW", "0.60")
        )
        
        # User Roles and Department Access
        self.USER_ROLES = self._parse_user_roles()
        self.DEPT_ACCESS = self._parse_department_access()
        
        # Set up logging
        self._setup_logging()
        
        # Initialize API clients
        self._anthropic_client = None
    
    def _setup_logging(self):
        """
        Configure comprehensive logging to both file and console.
        
        Creates structured logs for audit trail with:
        - Timestamp
        - Log level
        - Module name
        - Message
        """
        log_level = os.getenv("LOG_LEVEL", "INFO")
        log_file = os.getenv("LOG_FILE", "/app/logs/wren-bot.log")
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File formatter (detailed for audit trail)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console formatter (cleaner for live viewing)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler for audit trail
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)
        
        # Console handler for real-time monitoring
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(console_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Log startup
        logging.info("="*70)
        logging.info("WREN AI SLACK BOT - Configuration Initialized")
        logging.info("="*70)
        logging.info(f"Log file: {log_file}")
        logging.info(f"Log level: {log_level}")
        logging.info(f"Claude model: {self.ANTHROPIC_MODEL}")
        logging.info(f"Wren AI URL: {self.WREN_URL}")
        logging.info(f"Redshift host: {self.REDSHIFT_HOST}")
        logging.info("="*70)
    
    def _parse_user_roles(self) -> Dict[str, Dict[str, str]]:
        """
        Parse USER_ROLES environment variable.
        
        Format: SLACK_USER_ID:ROLE:DEPARTMENT
        Example: U01ABC:admin:all,U02DEF:analyst:sales
        
        Returns:
            Dictionary mapping Slack user IDs to role information:
            {
                'U01ABC': {'role': 'admin', 'department': 'all'},
                'U02DEF': {'role': 'analyst', 'department': 'sales'}
            }
        """
        roles_str = os.getenv("USER_ROLES", "")
        roles = {}
        
        if not roles_str:
            logging.warning("⚠️  No USER_ROLES configured - all users will be denied access")
            return roles
        
        for entry in roles_str.split(","):
            entry = entry.strip()
            if not entry:
                continue
            
            parts = entry.split(":")
            if len(parts) == 3:
                user_id, role, department = parts
                roles[user_id] = {
                    "role": role.strip(),
                    "department": department.strip()
                }
                logging.info(f"Loaded user role: {user_id} -> {role}/{department}")
            else:
                logging.warning(f"Invalid user role format: {entry}")
        
        logging.info(f"✅ Loaded {len(roles)} user role mappings")
        return roles
    
    def _parse_department_access(self) -> Dict[str, list]:
        """
        Parse department-specific table access rules.
        
        Returns:
            Dictionary mapping department names to allowed tables:
            {
                'sales': ['public.orders', 'public.customers'],
                'marketing': ['public.campaigns', 'public.leads']
            }
        """
        dept_access = {}
        
        # Get all DEPT_ACCESS_* environment variables
        for key, value in os.environ.items():
            if key.startswith("DEPT_ACCESS_"):
                dept_name = key.replace("DEPT_ACCESS_", "").lower()
                tables = [t.strip() for t in value.split(",") if t.strip()]
                dept_access[dept_name] = tables
                logging.info(f"Department access: {dept_name} -> {len(tables)} tables")
        
        return dept_access
    
    @property
    def anthropic_client(self) -> Anthropic:
        """
        Get or create Anthropic API client.
        
        Returns:
            Anthropic client instance for Claude API calls
        """
        if self._anthropic_client is None:
            self._anthropic_client = Anthropic(api_key=self.ANTHROPIC_API_KEY)
            logging.info(f"✅ Anthropic client initialized with model: {self.ANTHROPIC_MODEL}")
        return self._anthropic_client
    
    def get_department_tables(self, department: str) -> Optional[list]:
        """
        Get list of tables accessible by a department.
        
        Args:
            department: Department name (e.g., 'sales', 'marketing')
        
        Returns:
            List of accessible table names, or None if no restrictions
        """
        if department == "all":
            return None  # Admin access, no restrictions
        
        return self.DEPT_ACCESS.get(department.lower(), [])
    
    def validate_configuration(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            True if valid, raises ValueError if invalid
        """
        required = {
            "ANTHROPIC_API_KEY": self.ANTHROPIC_API_KEY,
            "SLACK_BOT_TOKEN": self.SLACK_BOT_TOKEN,
            "SLACK_APP_TOKEN": self.SLACK_APP_TOKEN,
            "REDSHIFT_HOST": self.REDSHIFT_HOST,
            "REDSHIFT_DATABASE": self.REDSHIFT_DATABASE,
        }
        
        missing = [k for k, v in required.items() if not v]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        logging.info("✅ All required configuration validated")
        return True