from __future__ import annotations

import sqlite3

import database.connection as connection_module
from database.schema_initializer import initialize_schema


def test_initialize_schema_is_idempotent(tmp_path, monkeypatch) -> None:
    database_dir = tmp_path / "storage"
    database_path = database_dir / "test.db"

    monkeypatch.setattr(
        connection_module,
        "DATABASE_DIR",
        database_dir,
    )
    monkeypatch.setattr(
        connection_module,
        "DATABASE_PATH",
        database_path,
    )

    initialize_schema()
    initialize_schema()

    with sqlite3.connect(database_path) as connection:
        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """).fetchall()

    assert ("players",) in tables


def test_players_table_contains_expected_columns(tmp_path, monkeypatch) -> None:
    database_dir = tmp_path / "storage"
    database_path = database_dir / "test.db"

    monkeypatch.setattr(
        connection_module,
        "DATABASE_DIR",
        database_dir,
    )
    monkeypatch.setattr(
        connection_module,
        "DATABASE_PATH",
        database_path,
    )

    initialize_schema()

    with sqlite3.connect(database_path) as connection:
        columns = connection.execute("PRAGMA table_info(players)").fetchall()

    column_names = {column[1] for column in columns}

    assert column_names == {
        "discord_id",
        "name",
        "level",
        "experience",
        "hp",
        "max_hp",
        "attack",
        "defense",
        "gold",
    }
