"""
Wren AI Slack Bot - Main Entry Point

Production-ready bot for querying AWS Redshift data warehouse
via natural language using Wren AI and Claude Sonnet 4.5.

Features:
- Natural language to SQL via Wren AI
- Row-level security (department-based filtering)
- SQL validation and safety checks
- Query explanations via Claude
- CSV/JSON/Chart exports
- Progressive clarifications
- Comprehensive audit logging

Usage:
    python src/main.py

Environment variables required (see .env.example):
    - WREN_URL, ANTHROPIC_API_KEY, SLACK_BOT_TOKEN, SLACK_APP_TOKEN
    - REDSHIFT_HOST, REDSHIFT_DATABASE, REDSHIFT_USER, REDSHIFT_PASSWORD
    - USER_ROLES
"""

import asyncio
import logging
import sys
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

# Fixed imports - all without 'src.' prefix
from config import Config
from wren_client import WrenClient
from slack_bot import SlackBot
from security import RowLevelSecurity
from explainer import QueryExplainer
from validator import SQLValidator
from export_handler import ExportHandler

logger = logging.getLogger(__name__)


async def main():
    """
    Initialize and start the Wren AI Slack Bot.
    
    Flow:
    1. Load configuration
    2. Initialize all components
    3. Run health checks
    4. Start Slack socket mode handler
    """
    
    try:
        logger.info("="*70)
        logger.info("🚀 STARTING WREN AI SLACK BOT")
        logger.info("="*70)
        
        # Load and validate configuration
        logger.info("Loading configuration...")
        config = Config()
        config.validate_configuration()
        
        # Initialize Wren AI client
        logger.info("Initializing Wren AI client...")
        wren = WrenClient(
            base_url=config.WREN_URL,
            timeout=config.MAX_QUERY_TIMEOUT_SECONDS
        )
        
        # Initialize security (RLS)
        logger.info("Initializing row-level security...")
        rls = RowLevelSecurity(
            user_roles=config.USER_ROLES,
            dept_access=config.DEPT_ACCESS
        )
        
        # Initialize query explainer (Claude)
        logger.info("Initializing query explainer...")
        explainer = QueryExplainer(
            anthropic_client=config.anthropic_client,
            model=config.ANTHROPIC_MODEL
        )
        
        # Initialize SQL validator
        logger.info("Initializing SQL validator...")
        validator = SQLValidator()
        
        # Initialize export handler
        logger.info("Initializing export handler...")
        export_handler = ExportHandler(
            enable_csv=config.ENABLE_CSV_EXPORT,
            enable_json=config.ENABLE_JSON_EXPORT,
            enable_charts=config.ENABLE_CHARTS,
            max_export_rows=config.MAX_ROWS_EXPORT
        )
        
        # Initialize Slack app
        logger.info("Initializing Slack app...")
        app = AsyncApp(
            token=config.SLACK_BOT_TOKEN,
            signing_secret=config.SLACK_SIGNING_SECRET
        )
        
        # Initialize bot with all components (now accepts config)
        logger.info("Initializing Slack bot orchestrator...")
        bot = SlackBot(
            app=app,
            wren=wren,
            rls=rls,
            explainer=explainer,
            validator=validator,
            export_handler=export_handler,
            config=config  # Pass config for settings
        )
        
        # Run health check
        logger.info("Running health check on Wren AI...")
        if not await wren.health_check():
            logger.error("❌ Wren AI health check failed!")
            logger.error("Please ensure:")
            logger.error("  1. Wren AI service is running: docker-compose ps")
            logger.error("  2. WREN_URL is correct in .env")
            logger.error("  3. Wren AI can connect to Redshift")
            logger.error("  4. Check Wren AI logs: docker-compose logs wren-ai")
            raise Exception("Wren AI is not healthy - cannot start bot")
        
        # Success! Show startup summary
        logger.info("")
        logger.info("="*70)
        logger.info("✅ WREN AI SLACK BOT STARTED SUCCESSFULLY")
        logger.info("="*70)
        logger.info(f"📊 Wren AI: {config.WREN_URL}")
        logger.info(f"🤖 Claude Model: {config.ANTHROPIC_MODEL}")
        logger.info(f"🗄️  Database: Redshift ({config.REDSHIFT_HOST})")
        logger.info(f"👥 Configured users: {len(config.USER_ROLES)}")
        logger.info(f"🏢 Departments: {len(config.DEPT_ACCESS)}")
        logger.info("")
        logger.info("Features enabled:")
        logger.info(f"  📥 CSV Export: {'✅' if config.ENABLE_CSV_EXPORT else '❌'}")
        logger.info(f"  📄 JSON Export: {'✅' if config.ENABLE_JSON_EXPORT else '❌'}")
        logger.info(f"  📊 Charts: {'✅' if config.ENABLE_CHARTS else '❌'}")
        logger.info(f"  💬 Clarifications: {'✅' if config.ENABLE_PROGRESSIVE_CLARIFICATION else '❌'}")
        logger.info(f"  🔍 Suggestions: {'✅' if config.ENABLE_ALTERNATIVE_SUGGESTIONS else '❌'}")
        logger.info("")
        logger.info("💬 Listening for /ask commands in Slack...")
        logger.info("💡 Try: /ask How many users do we have?")
        logger.info("="*70)
        logger.info("")
        
        # Start Slack socket mode handler
        handler = AsyncSocketModeHandler(app, config.SLACK_APP_TOKEN)
        await handler.start_async()
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("="*70)
        logger.info("⚠️  Shutdown signal received")
        logger.info("="*70)
        logger.info("Closing connections...")
        
        # Cleanup
        if 'wren' in locals():
            await wren.close()
        
        logger.info("✅ Shutdown complete")
        logger.info("="*70)
    
    except Exception as e:
        logger.error("")
        logger.error("="*70)
        logger.error("❌ FATAL ERROR - Bot failed to start")
        logger.error("="*70)
        logger.error(f"Error: {str(e)}")
        logger.error("", exc_info=True)
        logger.error("="*70)
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("  1. Check .env file has all required variables:")
        logger.error("     - ANTHROPIC_API_KEY")
        logger.error("     - SLACK_BOT_TOKEN, SLACK_APP_TOKEN")
        logger.error("     - REDSHIFT_HOST, REDSHIFT_DATABASE")
        logger.error("     - USER_ROLES")
        logger.error("  2. Verify Slack tokens are correct")
        logger.error("  3. Ensure Wren AI service is running:")
        logger.error("     docker-compose ps")
        logger.error("  4. Verify Redshift credentials and network access")
        logger.error("  5. Check logs above for specific error details")
        logger.error("  6. Try: docker-compose logs wren-ai")
        logger.error("="*70)
        
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())