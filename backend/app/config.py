import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = Path("/tmp/datavera_sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration settings
SESSION_INACTIVITY_TIMEOUT_MINUTES = int(os.getenv("SESSION_INACTIVITY_TIMEOUT_MINUTES", "30"))
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(150 * 1024 * 1024))) # 150 MB

# LLM Configurations
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "groq") # groq or gemini
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Query execution constraints
MAX_QUERY_EXECUTION_SECONDS = float(os.getenv("MAX_QUERY_EXECUTION_SECONDS", "10.0"))
MAX_ROW_LIMIT = int(os.getenv("MAX_ROW_LIMIT", "1000"))
