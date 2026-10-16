"""Sensor data source — mock field sensors for the hackathon MVP."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def fetch_sensor_data(field_id: str = "field-01") -> dict[str, Any]:
    # Replace with real IoT / API later.
    return {
        "source": "mock-sensors",
        "field_id": field_id,
        "soil_moisture_pct": 34.0,
        "soil_temp_c": 16.2,
        "leaf_wetness": False,
        "battery_pct": 87,
        "measured_at": datetime.now(timezone.utc).isoformat(),
    }
