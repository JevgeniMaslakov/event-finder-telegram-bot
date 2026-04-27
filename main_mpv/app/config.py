import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./event_finder.db")
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY", "")
PREDICTHQ_API_TOKEN = os.getenv("PREDICTHQ_API_TOKEN", "")
SYNC_CITY = os.getenv("SYNC_CITY", "Tallinn")
SYNC_COUNTRY_CODE = os.getenv("SYNC_COUNTRY_CODE", "EE")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")