"""
Configuration Module

Manages environment variables, logging setup, and application configuration
for Wren AI Data Assistant (Streamlit).
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()


class Config:
    """
    Central configuration manager for the Wren AI Data Assistant.

    Handles:
    - Environment variable loading and validation
    - Logging configuration
    - Claude/Anthropic client initialization
    - Database configuration
    """

    def __init__(self):
        """Initialize configuration and set up logging."""
        # Wren AI Configuration
        self.WREN_URL = os.getenv("WREN_URL", "http://wren-ai:8000")
        self.WREN_PROJECT_ID = os.getenv("WREN_PROJECT_ID", "analytics")
        self.WREN_MDL_HASH = os.getenv("WREN_MDL_HASH")  # Optional - auto-fetched if not set

        # Anthropic/Claude Configuration
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required")

        # Using Claude Sonnet 4.5
        self.ANTHROPIC_MODEL = os.getenv(
            "ANTHROPIC_MODEL",
            "claude-sonnet-4-20250514"
        )

        # Database Configuration (PostgreSQL by default)
        self.DB_TYPE = os.getenv("DB_TYPE", "postgres").lower()
        self.DB_HOST = os.getenv("DB_HOST", "postgres")
        self.DB_PORT = int(os.getenv("DB_PORT", "5432"))
        self.DB_DATABASE = os.getenv("DB_DATABASE", "analytics")
        self.DB_USER = os.getenv("DB_USER", "wren_user")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "wren_password")
        self.DB_SSL = os.getenv("DB_SSL", "false").lower() == "true"

        # Display & Export Settings
        self.MAX_ROWS_DISPLAY = int(os.getenv("MAX_ROWS_DISPLAY", "100"))
        self.MAX_ROWS_EXPORT = int(os.getenv("MAX_ROWS_EXPORT", "10000"))
        self.ENABLE_CSV_EXPORT = os.getenv("ENABLE_CSV_EXPORT", "true").lower() == "true"
        self.ENABLE_JSON_EXPORT = os.getenv("ENABLE_JSON_EXPORT", "true").lower() == "true"
        self.ENABLE_CHARTS = os.getenv("ENABLE_CHARTS", "true").lower() == "true"

        # Query Settings
        self.MAX_QUERY_TIMEOUT_SECONDS = int(
            os.getenv("MAX_QUERY_TIMEOUT_SECONDS", "30")
        )

        # Set up logging
        self._setup_logging()

        # Initialize API clients
        self._anthropic_client = None

    def _setup_logging(self):
        """
        Configure logging to both file and console.

        Creates structured logs with:
        - Timestamp
        - Log level
        - Module name
        - Message
        """
        log_level = os.getenv("LOG_LEVEL", "INFO")
        log_file = os.getenv("LOG_FILE", "/app/logs/wren-app.log")

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
        logging.info("WREN AI DATA ASSISTANT - Configuration Initialized")
        logging.info("="*70)
        logging.info(f"Log file: {log_file}")
        logging.info(f"Log level: {log_level}")
        logging.info(f"Claude model: {self.ANTHROPIC_MODEL}")
        logging.info(f"Wren AI URL: {self.WREN_URL}")
        logging.info(f"Database: {self.DB_TYPE} @ {self.DB_HOST}")
        logging.info("="*70)

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

    def validate_configuration(self) -> bool:
        """
        Validate that all required configuration is present.

        Returns:
            True if valid, raises ValueError if invalid
        """
        required = {
            "ANTHROPIC_API_KEY": self.ANTHROPIC_API_KEY,
            "DB_HOST": self.DB_HOST,
            "DB_DATABASE": self.DB_DATABASE,
        }

        missing = [k for k, v in required.items() if not v]

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        logging.info("✅ All required configuration validated")
        return True
