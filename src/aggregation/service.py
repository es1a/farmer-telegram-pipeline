"""Aggregation service: NoSQL + weather + sensors → structured context."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.aggregation.sensors import fetch_sensor_data
from src.aggregation.weather import fetch_weather
from src.persistence.nosql import NoSQLStore


class AggregationService:
    def __init__(self, store: NoSQLStore) -> None:
        self.store = store

    async def build_context(self, message: dict[str, Any]) -> dict[str, Any]:
        weather = await fetch_weather()
        sensors = fetch_sensor_data()
        recent = self.store.list_messages(limit=5)

        context = {
            "aggregated_at": datetime.now(timezone.utc).isoformat(),
            "farmer_message": {
                "id": message.get("id"),
                "text": message.get("text"),
                "chat_id": message.get("chat_id"),
                "username": message.get("username"),
                "created_at": message.get("created_at"),
            },
            "recent_messages": [
                {"id": m.get("id"), "text": m.get("text"), "created_at": m.get("created_at")}
                for m in recent
            ],
            "weather": weather,
            "sensors": sensors,
        }
        self.store.log_event("aggregation", {"message_id": message.get("id")})
        return context
