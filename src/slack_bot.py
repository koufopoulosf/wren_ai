"""
Slack Bot - Main Orchestration

Complete implementation with:
- Progressive clarifications
- Entity suggestions
- Confidence-based workflows
- Export handling
- Comprehensive logging
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

logger = logging.getLogger(__name__)


class QueryLogger:
    """Structured logging for audit trail."""
    
    @staticmethod
    def log_query_start(user_id: str, username: str, question: str, dept: str):
        logger.info(f"QUERY_START | User={user_id} ({username}) | Dept={dept} | Q=\"{question}\"")
    
    @staticmethod
    def log_query_success(user_id: str, question: str, duration: float, rows: int):
        logger.info(f"QUERY_SUCCESS | User={user_id} | Duration={duration:.2f}s | Rows={rows}")
    
    @staticmethod
    def log_query_error(user_id: str, question: str, error: str):
        logger.error(f"QUERY_ERROR | User={user_id} | Error={error}")
    
    @staticmethod
    def log_export(user_id: str, export_type: str, rows: int):
        logger.info(f"EXPORT | User={user_id} | Type={export_type} | Rows={rows}")
    
    @staticmethod
    def log_clarification(user_id: str, question: str, reason: str):
        logger.info(f"CLARIFICATION | User={user_id} | Reason={reason}")


class SlackBot:
    """Main Slack bot with all features."""
    
    def __init__(
        self, app, wren, rls, explainer, validator, export_handler,
        max_rows_display=50, confidence_high=0.85, confidence_low=0.60,
        enable_clarification=True, enable_suggestions=True
    ):
        self.app = app
        self.wren = wren
        self.rls = rls
        self.explainer = explainer
        self.validator = validator
        self.export_handler = export_handler
        self.max_rows_display = max_rows_display
        self.confidence_high = confidence_high
        self.confidence_low = confidence_low
        self.enable_clarification = enable_clarification
        self.enable_suggestions = enable_suggestions
        
        self._register_handlers()
        logger.info("✅ Slack bot initialized")
    
    def _register_handlers(self):
        self.app.command("/ask")(self.handle_ask)
        self.app.action("approve_query")(self.handle_approval)
        self.app.action("cancel_query")(self.handle_cancel)
        self.app.action("export_csv")(self.handle_export_csv)
        self.app.action("export_json")(self.handle_export_json)
        self.app.action("show_chart")(self.handle_show_chart)
        self.app.action("feedback_helpful")(self.handle_feedback)
        self.app.action("feedback_not_helpful")(self.handle_feedback)
    
    async def _get_user_info(self, client, user_id: str) -> Dict:
        try:
            response = await client.users_info(user=user_id)
            user = response["user"]
            return {"id": user_id, "name": user.get("name", ""), "real_name": user.get("real_name", "")}
        except:
            return {"id": user_id, "name": "unknown", "real_name": "unknown"}
    
    async def handle_ask(self, ack, command, client):
        await ack()
        
        user_id = command["user_id"]
        question = command["text"].strip()
        channel_id = command["channel_id"]
        user_info_slack = await self._get_user_info(client, user_id)
        username = user_info_slack["real_name"]
        
        if not question:
            await client.chat_postMessage(channel=channel_id, text="❓ Please ask a question.\n\nExample: `/ask What was revenue last month?`")
            return
        
        try:
            if not self.rls.is_authorized(user_id):
                await client.chat_postMessage(channel=channel_id, text="🚫 Not authorized. Contact your admin.")
                return
            
            user_info = self.rls.get_user_info(user_id)
            dept = user_info["department"]
            QueryLogger.log_query_start(user_id, username, question, dept)
            
            thinking = await client.chat_postMessage(channel=channel_id, text=f"🤔 Analyzing: _{question}_")
            
            wren_response = await self.wren.ask_question(question, {"department": dept})
            sql = wren_response.get("sql", "")
            confidence = wren_response.get("confidence", 0.0)
            suggestions = wren_response.get("suggestions", [])
            
            if not sql:
                await self._handle_no_sql(client, channel_id, thinking["ts"], question, suggestions, user_id)
                return
            
            is_valid, error = self.validator.validate(sql)
            if not is_valid:
                await client.chat_postMessage(channel=channel_id, text=error)
                await client.chat_delete(channel=channel_id, ts=thinking["ts"])
                return
            
            if confidence < self.confidence_low and self.enable_clarification:
                await self._ask_clarification(client, channel_id, thinking["ts"], question, sql, suggestions)
                return
            
            explanation = await self.explainer.explain(sql)
            await self._show_approval(client, channel_id, question, sql, explanation, user_id, confidence)
            await client.chat_delete(channel=channel_id, ts=thinking["ts"])
        
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            await client.chat_postMessage(channel=channel_id, text=f"❌ Error: {str(e)}")
    
    async def _handle_no_sql(self, client, channel_id, ts, question, suggestions, user_id):
        text = "😕 I couldn't generate a query.\n\n"
        if suggestions and self.enable_suggestions:
            text += "*Did you mean:*\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions[:3]))
        else:
            text += "*Try:*\n• Be more specific\n• Include time period\n• Ask about known metrics"
        await client.chat_update(channel=channel_id, ts=ts, text=text)
    
    async def _ask_clarification(self, client, channel_id, ts, question, sql, suggestions):
        text = f"🤔 Not quite sure about: _{question}_\n\n"
        if suggestions:
            text += "*Did you mean:*\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions[:5]))
        else:
            text += "Please clarify:\n• Which metric?\n• Which time period?\n• Any filters?"
        await client.chat_update(channel=channel_id, ts=ts, text=text)
    
    async def _show_approval(self, client, channel_id, question, sql, explanation, user_id, confidence):
        emoji = "🟢" if confidence >= self.confidence_high else "🟡" if confidence >= self.confidence_low else "🟠"
        conf_text = "High confidence" if confidence >= self.confidence_high else "Medium confidence"
        filter_info = self.rls.explain_filter(user_id)
        
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"{emoji} *{conf_text}*"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*📝 Explanation:*\n{explanation}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*💻 SQL:*\n```{sql[:500]}```"}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": filter_info}]},
            {"type": "actions", "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "✅ Run"}, "style": "primary", 
                 "action_id": "approve_query", "value": json.dumps({"sql": sql, "question": question, "explanation": explanation})},
                {"type": "button", "text": {"type": "plain_text", "text": "❌ Cancel"}, "action_id": "cancel_query"}
            ]}
        ]
        await client.chat_postMessage(channel=channel_id, blocks=blocks, text=explanation)
    
    async def handle_approval(self, ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        ts = body["message"]["ts"]
        
        try:
            value = json.loads(body["actions"][0]["value"])
            sql, question = value["sql"], value["question"]
            
            await client.chat_update(channel=channel_id, ts=ts, text="⏳ Executing...")
            
            filtered_sql = self.rls.apply_filter(sql, user_id)
            start = time.time()
            results = await self.wren.execute_sql(filtered_sql)
            duration = time.time() - start
            
            QueryLogger.log_query_success(user_id, question, duration, len(results))
            await self._show_results(client, channel_id, ts, results, duration, question, user_id)
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            await client.chat_update(channel=channel_id, ts=ts, text=f"❌ Failed: {str(e)}")
    
    def _format_results(self, results: list, max_rows: int = None) -> str:
        if not results:
            return "📭 No results"
        max_rows = max_rows or self.max_rows_display
        display = results[:max_rows]
        
        if len(display) == 1 and len(display[0]) == 1:
            k, v = list(display[0].items())[0]
            return f"*{k}:* `{v}`"
        
        lines = [f"{i+1}. " + " | ".join(f"*{k}:* `{v}`" for k,v in row.items()) for i, row in enumerate(display)]
        text = "\n".join(lines)
        if len(results) > max_rows:
            text += f"\n\n_...and {len(results)-max_rows} more rows_"
        return text
    
    async def _show_results(self, client, channel_id, ts, results, duration, question, user_id):
        text = self._format_results(results)
        actions = []
        
        if self.export_handler.enable_csv and results:
            actions.append({"type": "button", "text": {"type": "plain_text", "text": "📥 CSV"}, 
                          "action_id": "export_csv", "value": json.dumps({"results": results, "question": question})})
        if self.export_handler.enable_json and results:
            actions.append({"type": "button", "text": {"type": "plain_text", "text": "📄 JSON"}, 
                          "action_id": "export_json", "value": json.dumps({"results": results, "question": question})})
        if self.export_handler.can_generate_chart(results):
            actions.append({"type": "button", "text": {"type": "plain_text", "text": "📊 Chart"}, 
                          "action_id": "show_chart", "value": json.dumps({"results": results, "question": question})})
        
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": f"✅ *Results* ({duration:.1f}s | {len(results)} rows)\n\n{text}"}}]
        if actions:
            blocks.append({"type": "actions", "elements": actions})
        blocks.append({"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "👍 Helpful"}, 
             "action_id": "feedback_helpful", "value": json.dumps({"question": question})},
            {"type": "button", "text": {"type": "plain_text", "text": "👎 Not helpful"}, 
             "action_id": "feedback_not_helpful", "value": json.dumps({"question": question})}
        ]})
        
        await client.chat_update(channel=channel_id, ts=ts, blocks=blocks, text=f"{len(results)} rows")
    
    async def handle_export_csv(self, ack, body, client):
        await ack()
        try:
            value = json.loads(body["actions"][0]["value"])
            results, question = value["results"], value["question"]
            csv_bytes = self.export_handler.to_csv(results)
            if csv_bytes:
                await client.files_upload_v2(channel=body["channel"]["id"], file=csv_bytes, 
                                            filename="results.csv", title=f"Results: {question[:50]}")
                QueryLogger.log_export(body["user"]["id"], "CSV", len(results))
        except Exception as e:
            logger.error(f"CSV export error: {e}")
    
    async def handle_export_json(self, ack, body, client):
        await ack()
        try:
            value = json.loads(body["actions"][0]["value"])
            results, question = value["results"], value["question"]
            json_bytes = self.export_handler.to_json(results)
            if json_bytes:
                await client.files_upload_v2(channel=body["channel"]["id"], file=json_bytes, 
                                            filename="results.json", title=f"Results: {question[:50]}")
                QueryLogger.log_export(body["user"]["id"], "JSON", len(results))
        except Exception as e:
            logger.error(f"JSON export error: {e}")
    
    async def handle_show_chart(self, ack, body, client):
        await ack()
        try:
            value = json.loads(body["actions"][0]["value"])
            results, question = value["results"], value["question"]
            chart_bytes = self.export_handler.generate_chart(results, title=question[:100])
            if chart_bytes:
                await client.files_upload_v2(channel=body["channel"]["id"], file=chart_bytes, 
                                            filename="chart.png", title=f"Chart: {question[:50]}")
                QueryLogger.log_export(body["user"]["id"], "Chart", len(results))
        except Exception as e:
            logger.error(f"Chart error: {e}")
    
    async def handle_cancel(self, ack, body, client):
        await ack()
        await client.chat_update(channel=body["channel"]["id"], ts=body["message"]["ts"], text="❌ Cancelled")
    
    async def handle_feedback(self, ack, body, client):
        await ack()
        feedback = "positive" if "helpful" in body["actions"][0]["action_id"] else "negative"
        logger.info(f"FEEDBACK | User={body['user']['id']} | Type={feedback}")
        await client.chat_postEphemeral(channel=body["channel"]["id"], user=body["user"]["id"], text="Thanks! 🙏")