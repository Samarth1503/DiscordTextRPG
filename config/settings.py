from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment-specific .env or default .env
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
if ENVIRONMENT == "test":
    load_dotenv(BASE_DIR / ".env.test")
load_dotenv(BASE_DIR / ".env")


def get_required_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)

    if not value:
        raise RuntimeError(f"Required environment variable '{name}' is not configured.")

    return value


# Environment settings
IS_TEST_ENV = ENVIRONMENT == "test"
DISCORD_TOKEN = get_required_env(
    "DISCORD_TOKEN", default="MOCK_TEST_TOKEN" if IS_TEST_ENV else None
)
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

DATABASE_DIR = BASE_DIR / "storage"
DATABASE_PATH = DATABASE_DIR / ("test_game.db" if IS_TEST_ENV else "game.db")

# Game Balance Constants
DEFAULT_HP = 100
DEFAULT_MAX_HP = 100
DEFAULT_ATTACK = 10
DEFAULT_DEFENSE = 5
DEFAULT_GOLD = 0
MAX_CHARACTER_NAME_LENGTH = 32
