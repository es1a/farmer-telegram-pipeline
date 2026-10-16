import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OFFICER_CHAT_ID = os.getenv("OFFICER_CHAT_ID", "").strip()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()

DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "48.137154"))
DEFAULT_LON = float(os.getenv("DEFAULT_LON", "11.576124"))
DEFAULT_LOCATION_NAME = os.getenv("DEFAULT_LOCATION_NAME", "Munich")

DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "pipeline.json"
DASHBOARD_PATH = DATA_DIR / "dashboard.xlsx"
