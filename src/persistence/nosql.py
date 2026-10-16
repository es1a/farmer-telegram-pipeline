"""NoSQL persistence for structured farmer messages and pipeline events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tinydb import Query, TinyDB

from src.config import DATA_DIR, DB_PATH


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class NoSQLStore:
    def __init__(self, path: str | None = None) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(path or str(DB_PATH))
        self.messages = self._db.table("messages")
        self.events = self._db.table("events")

    def persist_farmer_message(
        self,
        *,
        chat_id: int,
        user_id: int,
        username: str | None,
        text: str,
        language: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "chat_id": chat_id,
            "user_id": user_id,
            "username": username,
            "text": text,
            "language": language,
            "channel": "telegram",
            "created_at": _utc_now(),
            "status": "received",
        }
        doc_id = self.messages.insert(record)
        record["id"] = doc_id
        return record

    def update_message(self, message_id: int, **fields: Any) -> None:
        self.messages.update(fields, doc_ids=[message_id])

    def list_messages(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.messages.all()
        for row in rows:
            row["id"] = row.doc_id
        return list(reversed(rows))[:limit]

    def log_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.insert(
            {
                "type": event_type,
                "payload": payload,
                "created_at": _utc_now(),
            }
        )

    def find_by_chat(self, chat_id: int) -> list[dict[str, Any]]:
        Message = Query()
        rows = self.messages.search(Message.chat_id == chat_id)
        for row in rows:
            row["id"] = row.doc_id
        return rows
