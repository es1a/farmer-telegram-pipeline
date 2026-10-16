"""Telegram interface — farmer writes a message; pipeline answers + notifies officer."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from src.aggregation.service import AggregationService
from src.config import OFFICER_CHAT_ID, TELEGRAM_BOT_TOKEN
from src.dashboard.export import append_dashboard_row
from src.persistence.nosql import NoSQLStore
from src.recommendation.service import RecommendationService

logger = logging.getLogger(__name__)


class FarmerPipelineBot:
    def __init__(self) -> None:
        if not TELEGRAM_BOT_TOKEN:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is missing. Copy .env.example to .env and add your bot token."
            )
        self.store = NoSQLStore()
        self.aggregation = AggregationService(self.store)
        self.recommendation = RecommendationService()
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_cmd))
        self.app.add_handler(CommandHandler("status", self.status))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.effective_chat and update.message
        await update.message.reply_text(
            "Hello! I'm your farm assistant on Telegram.\n\n"
            "Describe a field problem in a normal message "
            "(pests, water, weather, fertilizer, …).\n\n"
            f"Your chat id: `{update.effective_chat.id}`\n"
            "Commands: /help /status",
            parse_mode="Markdown",
        )

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.message
        await update.message.reply_text(
            "Just write your problem in plain text.\n"
            "Example: \"Leaves have yellow spots and look dry.\"\n\n"
            "/status — last stored messages\n"
            "/start — show chat id (needed for officer notifications)"
        )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.message
        rows = self.store.list_messages(limit=5)
        if not rows:
            await update.message.reply_text("No messages stored yet.")
            return
        lines = [
            f"• [{m.get('created_at', '')[:19]}] {m.get('text', '')[:80]}"
            for m in rows
        ]
        await update.message.reply_text("Recent messages:\n" + "\n".join(lines))

    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.effective_user or not update.effective_chat:
            return

        text = (update.message.text or "").strip()
        if not text:
            return

        logger.info("Farmer message from %s: %s", update.effective_user.id, text)

        # 1) Persist structured call/message data (NoSQL)
        message = self.store.persist_farmer_message(
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
            username=update.effective_user.username,
            text=text,
            language=update.effective_user.language_code,
        )

        # 2) Aggregate NoSQL + weather + sensors
        context_data = await self.aggregation.build_context(message)

        # 3) Recommendation → answer farmer, optionally notify officer
        result = self.recommendation.recommend(context_data)

        self.store.update_message(
            message["id"],
            status="answered",
            topic=result["topic"],
            urgency=result["urgency"],
            answer=result["farmer_answer"],
        )
        self.store.log_event(
            "recommendation",
            {"message_id": message["id"], "topic": result["topic"], "urgency": result["urgency"]},
        )

        # 4) Dashboard / Excel export from aggregation + recommendation
        append_dashboard_row(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": message["id"],
                "chat_id": message["chat_id"],
                "username": message.get("username"),
                "farmer_text": text,
                "topic": result["topic"],
                "urgency": result["urgency"],
                "temp_c": (result["context_summary"]["weather"] or {}).get("temp_c"),
                "condition": (result["context_summary"]["weather"] or {}).get("condition"),
                "soil_moisture_pct": (result["context_summary"]["sensors"] or {}).get(
                    "soil_moisture_pct"
                ),
                "officer_notified": bool(result["officer_notify"] and OFFICER_CHAT_ID),
            }
        )

        await update.message.reply_text(result["farmer_answer"])

        if result["officer_notify"] and OFFICER_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=int(OFFICER_CHAT_ID),
                    text=result["officer_message"],
                )
            except Exception:
                logger.exception("Failed to notify officer chat_id=%s", OFFICER_CHAT_ID)

    def run(self) -> None:
        logger.info("Starting Telegram farmer pipeline bot…")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
