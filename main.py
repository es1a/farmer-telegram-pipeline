"""Farmer states a problem via Telegram."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    await update.message.reply_text("Send me your field problem as a text message.")


async def on_problem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message and update.effective_user
    text = (update.message.text or "").strip()
    if not text:
        return
    logging.info("Farmer %s stated problem: %s", update.effective_user.id, text)
    await update.message.reply_text("Got it — your problem was received.")


def main() -> None:
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_problem))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
