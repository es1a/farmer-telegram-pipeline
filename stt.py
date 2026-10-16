"""Speech-to-text for Telegram voice notes (OGG/Opus → text via OpenAI Whisper)."""

from __future__ import annotations

import io
import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class TranscriptionError(RuntimeError):
    pass


async def transcribe_voice(audio: bytes, filename: str = "voice.ogg") -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("WHISPER_MODEL", "whisper-1").strip()
    language = os.getenv("WHISPER_LANGUAGE", "").strip()

    if not api_key:
        raise TranscriptionError("Set OPENAI_API_KEY in .env to enable voice messages")
    if not audio:
        raise TranscriptionError("Empty audio")

    client = AsyncOpenAI(api_key=api_key)
    kwargs: dict = {
        "model": model,
        "file": (filename, io.BytesIO(audio), "audio/ogg"),
        "response_format": "text",
    }
    if language:
        kwargs["language"] = language

    result = await client.audio.transcriptions.create(**kwargs)
    text = (result if isinstance(result, str) else getattr(result, "text", str(result))).strip()
    if not text:
        raise TranscriptionError("Whisper returned empty transcript")
    logger.info("Transcribed %s bytes → %s chars", len(audio), len(text))
    return text
