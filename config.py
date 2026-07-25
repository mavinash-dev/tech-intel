import os
from dotenv import load_dotenv

load_dotenv()

# --- Database ---
DB_PATH = os.getenv("DB_PATH", "tech_intel.db")          # local SQLite fallback
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")  # e.g. https://xxx.turso.io
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

# --- AI ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# --- Reddit (optional) ---
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "tech-intel/1.0")

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

BRIEFING_STYLE = os.getenv("BRIEFING_STYLE", "beginner")
INGESTION_INTERVAL_MINUTES = int(os.getenv("INGESTION_INTERVAL_MINUTES", "30"))
