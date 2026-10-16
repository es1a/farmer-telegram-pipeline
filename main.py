"""Farmer states a problem via Telegram; teammates consume via HTTP/WebSocket."""

from __future__ import annotations

import asyncio
import logging
import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from api import PROBLEMS_PATH, app as fastapi_app, publish_problem
from stt import TranscriptionError, transcribe_voice


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
API_HOST = os.getenv("API_HOST", "0.0.0.0").strip()
API_PORT = int(os.getenv("API_PORT", "8000"))
MAX_VOICE_BYTES = int(os.getenv("MAX_VOICE_BYTES", str(5 * 1024 * 1024)))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    await update.message.reply_text(
        "Send me your field problem as text or a voice message."
    )


async def _save_problem(update: Update, text: str, *, source: str) -> None:
    assert update.message and update.effective_user and update.effective_chat
    user = update.effective_user
    record = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "chat_id": update.effective_chat.id,
        "problem": text,
        "source": source,
        "received_at": update.message.date.isoformat(),
    }
    await publish_problem(record)
    logging.info("Saved + broadcast %s problem from farmer %s: %s", source, user.id, text)
    await update.message.reply_text("Got it — your problem was received.")


async def on_problem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    text = (update.message.text or "").strip()
    if not text:
        return
    await _save_problem(update, text, source="text")


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message and update.message.voice
    voice = update.message.voice
    await update.message.reply_text("Got your voice note — transcribing…")

    try:
        if voice.file_size and voice.file_size > MAX_VOICE_BYTES:
            await update.message.reply_text("Voice note is too long. Please send a shorter one.")
            return

        file = await context.bot.get_file(voice.file_id)
        audio = bytes(await file.download_as_bytearray())
        if len(audio) > MAX_VOICE_BYTES:
            await update.message.reply_text("Voice note is too long. Please send a shorter one.")
            return

        text = await transcribe_voice(audio)
    except TranscriptionError as exc:
        logging.warning("Voice transcription failed: %s", exc)
        await update.message.reply_text(
            "Sorry, I could not understand that voice note. Please try again or send text."
        )
        return
    except Exception:
        logging.exception("Unexpected voice handling error")
        await update.message.reply_text(
            "Sorry, something went wrong with the voice note. Please send text instead."
        )
        return

    await update.message.reply_text(f"I heard: {text}")
    await _save_problem(update, text, source="voice")


async def run() -> None:
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_problem))
    bot_app.add_handler(MessageHandler(filters.VOICE, on_voice))

    config = uvicorn.Config(
        fastapi_app,
        host=API_HOST,
        port=API_PORT,
        log_level="info",
        lifespan="off",
    )
    server = uvicorn.Server(config)

    logging.info("Writing problems to %s", PROBLEMS_PATH)
    logging.info("API: http://%s:%s/problems  WS: ws://%s:%s/ws/problems", API_HOST, API_PORT, API_HOST, API_PORT)

    async with bot_app:
        await bot_app.start()
        assert bot_app.updater is not None
        await bot_app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        try:
            await server.serve()
        finally:
            await bot_app.updater.stop()
            await bot_app.stop()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
