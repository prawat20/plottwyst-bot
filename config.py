from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Discord ───────────────────────────────────────────────────────────────────
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")

# ─── Gemini AI ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
GEMINI_MODEL: str   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ─── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://localhost/plottwyst"
)

# ─── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

# ─── Game Timers (seconds) ─────────────────────────────────────────────────────
DISCUSSION_TIME: int = int(os.getenv("DISCUSSION_TIME", "60"))
VOTING_TIME:     int = int(os.getenv("VOTING_TIME",     "30"))
GUESS_TIME:      int = int(os.getenv("GUESS_TIME",      "30"))

# ─── Local Testing ─────────────────────────────────────────────────────────────
# Set TEST_MODE=true to skip Gemini and use pre-written sample cases instead.
TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() == "true"

# Comma-separated Discord user IDs that are always treated as premium.
# Used for dev/testing. E.g. PREMIUM_USER_IDS=123456789,987654321
PREMIUM_USER_IDS: set[int] = {
    int(uid.strip())
    for uid in os.getenv("PREMIUM_USER_IDS", "").split(",")
    if uid.strip().isdigit()
}

# ─── Game Limits ───────────────────────────────────────────────────────────────
GAME_STATE_TTL:  int = 7200   # Redis TTL for a game session (2 hours)
MAX_ROUNDS:      int = 4
INITIAL_CLUES:   int = 3
