"""Recommendation service: turn aggregated context into farmer answer + officer alert."""

from __future__ import annotations

from typing import Any


class RecommendationService:
    def recommend(self, context: dict[str, Any]) -> dict[str, Any]:
        text = (context.get("farmer_message") or {}).get("text") or ""
        weather = context.get("weather") or {}
        sensors = context.get("sensors") or {}

        lower = text.lower()
        urgency = "normal"
        topic = "general"
        actions: list[str] = []

        if any(k in lower for k in ("pest", "insect", "worm", "fungus", "disease", "blight")):
            topic = "pest_disease"
            urgency = "high"
            actions.append("Inspect affected plants and take clear photos of leaves/stems.")
            actions.append("Isolate heavily affected plants if possible.")
        elif any(k in lower for k in ("drought", "dry", "irrigation", "water", "wilt")):
            topic = "water"
            urgency = "high" if sensors.get("soil_moisture_pct", 50) < 30 else "medium"
            actions.append("Check irrigation schedule for the next 24h.")
            actions.append("Prioritize watering zones with lowest soil moisture.")
        elif any(k in lower for k in ("rain", "flood", "storm", "hail")):
            topic = "weather_risk"
            urgency = "medium"
            actions.append("Secure loose equipment and check drainage.")
        elif any(k in lower for k in ("fertilizer", "nutrient", "yellow", "growth")):
            topic = "nutrition"
            actions.append("Note crop type and last fertilizer application date.")
        else:
            actions.append("Share crop type, field location, and when the issue started.")

        soil = sensors.get("soil_moisture_pct")
        temp = weather.get("temp_c")
        condition = weather.get("condition")

        farmer_answer = (
            f"Thanks — I received your message.\n\n"
            f"Topic: {topic.replace('_', ' ')}\n"
            f"Urgency: {urgency}\n\n"
            f"Field snapshot:\n"
            f"• Weather: {temp}°C, {condition}\n"
            f"• Soil moisture: {soil}%\n\n"
            f"Suggested next steps:\n"
            + "\n".join(f"{i}. {a}" for i, a in enumerate(actions, 1))
        )

        officer_notify = urgency in {"high", "medium"}
        officer_message = (
            f"Farmer alert ({urgency})\n"
            f"Topic: {topic}\n"
            f"Message: {text}\n"
            f"Soil moisture: {soil}% | Weather: {temp}°C, {condition}"
        )

        return {
            "topic": topic,
            "urgency": urgency,
            "actions": actions,
            "farmer_answer": farmer_answer,
            "officer_notify": officer_notify,
            "officer_message": officer_message,
            "context_summary": {
                "weather": weather,
                "sensors": sensors,
            },
        }
