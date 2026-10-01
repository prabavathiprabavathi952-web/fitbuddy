"""Central configuration. All secrets come from environment variables / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")


def _clean_key(value: str | None) -> str:
    """Return the API key, or '' if it is missing or still the placeholder."""
    value = (value or "").strip().strip('"').strip("'")
    if not value or value.lower().startswith("your_"):
        return ""
    return value


GEMINI_API_KEY = _clean_key(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro").strip()
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash").strip()
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "90"))

DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{(PROJECT_ROOT / 'fitbuddy.db').as_posix()}"
)
# Render/Heroku give "postgres://..."; SQLAlchemy needs "postgresql://..."
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
