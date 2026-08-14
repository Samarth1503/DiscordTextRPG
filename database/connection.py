from __future__ import annotations

import sqlite3

from config.settings import DATABASE_DIR, DATABASE_PATH, IS_TEST_ENV


def initialize_database_directory() -> None:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    initialize_database_directory()

    target_path = str(db_path or DATABASE_PATH)
    connection = sqlite3.connect(target_path)
    connection.row_factory = sqlite3.Row

    # Configure production-ready SQLite PRAGMAs
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA busy_timeout = 5000;")

    if not IS_TEST_ENV and target_path != ":memory:":
        try:
            connection.execute("PRAGMA journal_mode = WAL;")
            connection.execute("PRAGMA synchronous = NORMAL;")
        except sqlite3.OperationalError:
            pass

    return connection
