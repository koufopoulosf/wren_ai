"""
Slack Bot - Main Orchestration

Complete implementation with:
- Progressive clarifications
- Entity suggestions
- Confidence-based workflows
- Export handling
- Comprehensive logging
- Config-driven settings
"""

import logging
import json
import time
from typing import Dict, Optional, List
from datetime import datetime
from slack_bolt.async_app import AsyncApp
from fuzzywuzzy import fuzz, process

from wren_client import WrenClient
from security import RowLevelSecurity
from explainer import QueryExplainer
from validator import SQLValidator
from export_handler import ExportHandler
from config import Config

logger = logging.getLogger(__name__)


class QueryLogger:
    """Structured logging for audit trail."""
    
    @staticmethod
    def log_query_start(user_id: str, username: str, question: str, dept: str):
        """Log when a query starts."""
        logger.info(
            f"QUERY_START | User={user_id} ({username}) | Dept={dept} | Q=\"{question}\""
        )
    
    @staticmethod
    def log_query_success(user_id: str, question: str, duration: float, rows: int):
        """Log successful query execution."""
        logger.info(
            f"QUERY_SUCCESS | User={user_id} | Duration={duration:.2f}s | Rows={rows} | Q=\"{question[:50]}\""
        )
    
    @staticmethod
    def log_query_error(user_id: str, question: str, error: str):
        """Log query errors."""
        logger.error(
            f"QUERY_ERROR | User={user_id} | Error={error} | Q=\"{question[:50]}\""
        )
    
    @staticmethod
    def log_export(user_id: str, export_type: str, rows: int):
        """Log data exports."""
        logger.info(
            f"EXPORT | User={user_id} | Type={export_type} | Rows={rows}"
        )
    
    @staticmethod
    def log_clarification(user_id: str, question: str, reason: str):
        """Log when clarification is needed."""
        logger.info(
            f"CLARIFICATION | User={user_id} | Reason={reason} | Q=\"{question[:50]}\""
        )


class SlackBot:
    """
    Main Slack bot orchestrator with all features.
    
    Handles:
    - /ask slash command
    - Progressive clarifications
    - Confidence-based workflows
    - Query approval and execution
    - Export generation (CSV/JSON/Charts)
    - Comprehensive audit logging
    """
    
    def __init__(
        self, 
        app: AsyncApp,
        wren: WrenClient,
        rls: RowLevelSecurity,
        explainer: QueryExplainer,
        validator: SQLValidator,
        export_handler: ExportHandler,
        config: Config  # Now accepts config
    ):
        """
        Initialize bot with all components.
        
        Args:
            app: Slack Bolt async app
            wren: Wren AI client
            rls: Row-level security handler
            explainer: Query explainer
            validator: SQL validator
            export_handler: Export handler
            config: Configuration object
        """
        self.app = app
        self.wren = wren
        self.rls = rls
        self.explainer = explainer
        self.validator = validator
        self.export_handler = export_handler
        
        # Use config values instead of hardcoded defaults
        self.max_rows_display = config.MAX_ROWS_DISPLAY
        self.confidence_high = config.CONFIDENCE_THRESHOLD_HIGH
        self.confidence_low = config.CONFIDENCE_THRESHOLD_LOW
        self.enable_clarification = config.ENABLE_PROGRESSIVE_CLARIFICATION
        self.enable_suggestions = config.ENABLE_ALTERNATIVE_SUGGESTIONS
        
        # Register Slack handlers
        self._register_handlers()
        
        logger.info("✅ Slack bot initialized with config-driven settings")
        logger.info(f"  Max rows display: {self.max_rows_display}")
        logger.info(f"  Confidence thresholds: high={self.confidence_high}, low={self.confidence_low}")
        logger.info(f"  Clarifications: {self.enable_clarification}")
        logger.info(f"  Suggestions: {self.enable_suggestions}")
    
    def _register_handlers(self):
        """Register all Slack command and action handlers."""
        self.app.command("/ask")(self.handle_ask)
        self.app.action("approve_query")(self.handle_approval)
        self.app.action("cancel_query")(self.handle_cancel)
        self.app.action("export_csv")(self.handle_export_csv)
        self.app.action("export_json")(self.handle_export_json)
        self.app.action("show_chart")(self.handle_show_chart)
        self.app.action("feedback_helpful")(self.handle_feedback)
        self.app.action("feedback_not_helpful")(self.handle_feedback)
    
    async def _get_user_info(self, client, user_id: str) -> Dict:
        """
        Get user information from Slack API.
        
        Args:
            client: Slack client
            user_id: Slack user ID
        
        Returns:
            Dict with user info (name, real_name, etc.)
        """
        try:
            response = await client.users_info(user=user_id)
            user = response["user"]
            return {
                "id": user_id,
                "name": user.get("name", "unknown"),
                "real_name": user.get("real_name", "unknown")
            }
        except Exception as e:
            logger.warning(f"Failed to get user info for {user_id}: {e}")
            return {"id": user_id, "name": "unknown", "real_name": "unknown"}
    
    async def handle_ask(self, ack, command, client):
        """
        Handle /ask slash command.
        
        Flow:
        1. Acknowledge immediately
        2. Validate user authorization
        3. Query Wren AI
        4. Check confidence level
        5. Show clarification OR approval UI
        """
        await ack()
        
        user_id = command["user_id"]
        question = command["text"].strip()
        channel_id = command["channel_id"]
        
        # Get user details from Slack
        user_info_slack = await self._get_user_info(client, user_id)
        username = user_info_slack["real_name"]
        
        if not question:
            await client.chat_postMessage(
                channel=channel_id,
                text="❓ Please ask a question.\n\n*Example:* `/ask What was revenue last month?`"
            )
            return
        
        try:
            # Check if user is authorized
            if not self.rls.is_authorized(user_id):
                logger.warning(f"Unauthorized access attempt by {user_id}")
                await client.chat_postMessage(
                    channel=channel_id,
                    text=(
                        "🚫 You are not authorized to use this bot.\n\n"
                        "Please contact your administrator to get access.\n"
                        "Your Slack user ID: `{user_id}`"
                    )
                )
                return
            
            # Get user role info
            user_info = self.rls.get_user_info(user_id)
            dept = user_info["department"]
            
            # Log query start
            QueryLogger.log_query_start(user_id, username, question, dept)
            
            # Show "thinking" message
            thinking = await client.chat_postMessage(
                channel=channel_id,
                text=f"🤔 Analyzing: _{question}_"
            )
            
            # Query Wren AI
            logger.info(f"Querying Wren AI for user {user_id}")
            wren_response = await self.wren.ask_question(
                question,
                user_context={"department": dept}
            )
            
            sql = wren_response.get("sql", "")
            confidence = wren_response.get("confidence", 0.0)
            suggestions = wren_response.get("suggestions", [])
            
            # Handle no SQL generated
            if not sql:
                QueryLogger.log_clarification(user_id, question, "No SQL generated")
                await self._handle_no_sql(
                    client, channel_id, thinking["ts"],
                    question, suggestions, user_id
                )
                return
            
            # Validate SQL
            is_valid, error = self.validator.validate(sql)
            if not is_valid:
                QueryLogger.log_query_error(user_id, question, f"Validation failed: {error}")
                await client.chat_postMessage(
                    channel=channel_id,
                    text=f"{error}\n\nPlease rephrase your question."
                )
                await client.chat_delete(channel=channel_id, ts=thinking["ts"])
                return
            
            # Check confidence level and decide flow
            if confidence < self.confidence_low and self.enable_clarification:
                QueryLogger.log_clarification(user_id, question, f"Low confidence: {confidence:.2f}")
                await self._ask_clarification(
                    client, channel_id, thinking["ts"],
                    question, sql, suggestions
                )
                return
            
            # Generate explanation
            explanation = await self.explainer.explain(sql)
            
            # Show approval UI
            await self._show_approval(
                client, channel_id, question, sql,
                explanation, user_id, confidence
            )
            
            # Delete thinking message
            await client.chat_delete(channel=channel_id, ts=thinking["ts"])
        
        except Exception as e:
            logger.error(f"Error in handle_ask for user {user_id}: {e}", exc_info=True)
            QueryLogger.log_query_error(user_id, question, str(e))
            
            await client.chat_postMessage(
                channel=channel_id,
                text=(
                    f"❌ Sorry, something went wrong: {str(e)}\n\n"
                    "Please try again or rephrase your question.\n"
                    "If the problem persists, contact your administrator."
                )
            )
    
    async def _handle_no_sql(
        self, client, channel_id: str, ts: str,
        question: str, suggestions: List, user_id: str
    ):
        """Handle case where Wren couldn't generate SQL."""
        text = "😕 I couldn't generate a query for that question.\n\n"
        
        if suggestions and self.enable_suggestions:
            text += "*Did you mean:*\n"
            text += "\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions[:3]))
            text += "\n\nOr try rephrasing your question."
        else:
            text += "*Try:*\n"
            text += "• Be more specific about what data you want\n"
            text += "• Include a time period (e.g., 'last month')\n"
            text += "• Ask about a specific metric (e.g., 'revenue', 'orders')\n\n"
            text += "*Examples:*\n"
            text += "• What was revenue last month?\n"
            text += "• Show top 10 customers by order count\n"
            text += "• How many active users do we have?"
        
        await client.chat_update(channel=channel_id, ts=ts, text=text)
    
    async def _ask_clarification(
        self, client, channel_id: str, ts: str,
        question: str, sql: str, suggestions: List
    ):
        """Ask user for clarification when confidence is low."""
        text = f"🤔 I'm not quite sure about: _{question}_\n\n"
        
        if suggestions and self.enable_suggestions:
            text += "*Did you mean one of these?*\n"
            text += "\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions[:5]))
            text += "\n\nPlease rephrase or choose from above."
        else:
            text += "Could you clarify:\n"
            text += "• What specific metric? (revenue, orders, users, etc.)\n"
            text += "• What time period? (today, this week, last month, etc.)\n"
            text += "• Any filters? (by region, department, status, etc.)"
        
        await client.chat_update(channel=channel_id, ts=ts, text=text)
    
    async def _show_approval(
        self, client, channel_id: str, question: str,
        sql: str, explanation: str, user_id: str, confidence: float
    ):
        """Show SQL approval message with Run/Cancel buttons."""
        # Confidence indicator
        if confidence >= self.confidence_high:
            emoji = "🟢"
            conf_text = "High confidence"
        elif confidence >= self.confidence_low:
            emoji = "🟡"
            conf_text = "Medium confidence - please verify"
        else:
            emoji = "🟠"
            conf_text = "Low confidence - please review carefully"
        
        # Get filter explanation
        filter_info = self.rls.explain_filter(user_id)
        
        # Truncate SQL if too long
        sql_display = sql[:500]
        if len(sql) > 500:
            sql_display += "\n... (truncated)"
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *{conf_text}*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📝 Explanation:*\n{explanation}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*💻 SQL:*\n```{sql_display}```"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": filter_info
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Run Query"},
                        "style": "primary",
                        "action_id": "approve_query",
                        "value": json.dumps({
                            "sql": sql,
                            "question": question,
                            "explanation": explanation
                        })
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Cancel"},
                        "action_id": "cancel_query"
                    }
                ]
            }
        ]
        
        await client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text=f"Query ready: {explanation}"
        )
    
    async def handle_approval(self, ack, body, client):
        """Handle user clicking "Run Query" button."""
        await ack()
        
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        ts = body["message"]["ts"]
        
        try:
            # Parse button value
            value = json.loads(body["actions"][0]["value"])
            sql = value["sql"]
            question = value["question"]
            
            # Update message to show executing
            await client.chat_update(
                channel=channel_id,
                ts=ts,
                text="⏳ Executing query...",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "⏳ *Executing query...*"
                    }
                }]
            )
            
            # Apply RLS filter
            filtered_sql = self.rls.apply_filter(sql, user_id)
            logger.info(f"Executing filtered SQL for user {user_id}")
            
            # Execute query
            start = time.time()
            results = await self.wren.execute_sql(filtered_sql)
            duration = time.time() - start
            
            # Log success
            QueryLogger.log_query_success(user_id, question, duration, len(results))
            
            # Show results
            await self._show_results(
                client, channel_id, ts,
                results, duration, question, user_id
            )
        
        except Exception as e:
            logger.error(f"Error executing query for {user_id}: {e}", exc_info=True)
            QueryLogger.log_query_error(
                user_id,
                question if 'question' in locals() else "unknown",
                str(e)
            )
            
            await client.chat_update(
                channel=channel_id,
                ts=ts,
                text=f"❌ Query failed: {str(e)}",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"❌ *Query failed:*\n{str(e)}\n\n"
                            "*Try:*\n"
                            "• Simplifying your question\n"
                            "• Adding more specific filters\n"
                            "• Choosing a shorter time period"
                        )
                    }
                }]
            )
    
    def _format_results(self, results: list, max_rows: int = None) -> str:
        """Format query results for Slack display."""
        if not results:
            return "📭 No results found."
        
        max_rows = max_rows or self.max_rows_display
        display = results[:max_rows]
        
        # Single value result
        if len(display) == 1 and len(display[0]) == 1:
            k, v = list(display[0].items())[0]
            return f"*{k}:* `{v}`"
        
        # Multiple rows - format as list
        lines = []
        for i, row in enumerate(display, 1):
            row_parts = [f"*{k}:* `{v}`" for k, v in row.items()]
            lines.append(f"{i}. {' | '.join(row_parts)}")
        
        text = "\n".join(lines)
        
        if len(results) > max_rows:
            text += f"\n\n_...and {len(results) - max_rows} more rows_"
        
        return text
    
    async def _show_results(
        self, client, channel_id: str, ts: str,
        results: list, duration: float, question: str, user_id: str
    ):
        """Show query results with export options."""
        text = self._format_results(results)
        
        # Build action buttons
        actions = []
        
        # Export buttons
        if self.export_handler.enable_csv and results:
            actions.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "📥 Download CSV"},
                "action_id": "export_csv",
                "value": json.dumps({"results": results, "question": question})
            })
        
        if self.export_handler.enable_json and results:
            actions.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "📄 Download JSON"},
                "action_id": "export_json",
                "value": json.dumps({"results": results, "question": question})
            })
        
        # Chart button (if data suitable)
        if self.export_handler.can_generate_chart(results):
            actions.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "📊 Show Chart"},
                "action_id": "show_chart",
                "value": json.dumps({"results": results, "question": question})
            })
        
        # Build blocks
        blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"✅ *Results* ({duration:.1f}s | {len(results)} rows)\n\n{text}"
            }
        }]
        
        # Add export actions if any
        if actions:
            blocks.append({
                "type": "actions",
                "elements": actions
            })
        
        # Add feedback buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "👍 Helpful"},
                    "action_id": "feedback_helpful",
                    "value": json.dumps({"question": question})
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "👎 Not helpful"},
                    "action_id": "feedback_not_helpful",
                    "value": json.dumps({"question": question})
                }
            ]
        })
        
        await client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=blocks,
            text=f"Results: {len(results)} rows"
        )
    
    async def handle_export_csv(self, ack, body, client):
        """Handle CSV export request."""
        await ack()
        
        try:
            value = json.loads(body["actions"][0]["value"])
            results = value["results"]
            question = value["question"]
            user_id = body["user"]["id"]
            channel_id = body["channel"]["id"]
            
            # Generate CSV
            csv_bytes = self.export_handler.to_csv(results)
            
            if csv_bytes:
                await client.files_upload_v2(
                    channel=channel_id,
                    file=csv_bytes,
                    filename="query_results.csv",
                    title=f"Results: {question[:50]}",
                    initial_comment="📥 Here's your data in CSV format"
                )
                
                QueryLogger.log_export(user_id, "CSV", len(results))
            else:
                await client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="❌ Failed to generate CSV export"
                )
        
        except Exception as e:
            logger.error(f"CSV export error: {e}", exc_info=True)
    
    async def handle_export_json(self, ack, body, client):
        """Handle JSON export request."""
        await ack()
        
        try:
            value = json.dumps(body["actions"][0]["value"])
            results = value["results"]
            question = value["question"]
            user_id = body["user"]["id"]
            channel_id = body["channel"]["id"]
            
            # Generate JSON
            json_bytes = self.export_handler.to_json(results)
            
            if json_bytes:
                await client.files_upload_v2(
                    channel=channel_id,
                    file=json_bytes,
                    filename="query_results.json",
                    title=f"Results: {question[:50]}",
                    initial_comment="📄 Here's your data in JSON format"
                )
                
                QueryLogger.log_export(user_id, "JSON", len(results))
            else:
                await client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="❌ Failed to generate JSON export"
                )
        
        except Exception as e:
            logger.error(f"JSON export error: {e}", exc_info=True)
    
    async def handle_show_chart(self, ack, body, client):
        """Handle chart generation request."""
        await ack()
        
        try:
            value = json.loads(body["actions"][0]["value"])
            results = value["results"]
            question = value["question"]
            user_id = body["user"]["id"]
            channel_id = body["channel"]["id"]
            
            # Generate chart
            chart_bytes = self.export_handler.generate_chart(
                results,
                chart_type="auto",
                title=question[:100]
            )
            
            if chart_bytes:
                await client.files_upload_v2(
                    channel=channel_id,
                    file=chart_bytes,
                    filename="chart.png",
                    title=f"Chart: {question[:50]}",
                    initial_comment="📊 Here's a visualization of your data"
                )
                
                QueryLogger.log_export(user_id, "Chart", len(results))
            else:
                await client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="❌ This data isn't suitable for chart generation"
                )
        
        except Exception as e:
            logger.error(f"Chart generation error: {e}", exc_info=True)
    
    async def handle_cancel(self, ack, body, client):
        """Handle cancel button."""
        await ack()
        
        channel_id = body["channel"]["id"]
        ts = body["message"]["ts"]
        user_id = body["user"]["id"]
        
        logger.info(f"User {user_id} cancelled query")
        
        await client.chat_update(
            channel=channel_id,
            ts=ts,
            text="❌ Query cancelled",
            blocks=[{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "❌ Query cancelled"
                }
            }]
        )
    
    async def handle_feedback(self, ack, body, client):
        """Handle feedback buttons."""
        await ack()
        
        action_id = body["actions"][0]["action_id"]
        user_id = body["user"]["id"]
        value = json.loads(body["actions"][0]["value"])
        question = value.get("question", "unknown")
        
        feedback = "positive" if "helpful" in action_id else "negative"
        
        logger.info(
            f"FEEDBACK | User={user_id} | Type={feedback} | Q=\"{question[:50]}\""
        )
        
        # Show thank you message
        await client.chat_postEphemeral(
            channel=body["channel"]["id"],
            user=user_id,
            text="Thanks for your feedback! 🙏"
        )