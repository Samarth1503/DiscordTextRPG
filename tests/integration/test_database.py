from __future__ import annotations

from database.connection import get_connection
from database.schema_initializer import initialize_schema


def test_database_connection_and_schema(tmp_path):
    db_file = tmp_path / "test_conn.db"
    conn = get_connection(str(db_file))

    # Check foreign keys PRAGMA
    fk_result = conn.execute("PRAGMA foreign_keys;").fetchone()
    assert fk_result[0] == 1
    conn.close()

    # Initialize schema
    conn = get_connection(str(db_file))
    initialize_schema(conn)

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()
    table_names = [t["name"] for t in tables]

    assert "players" in table_names
    assert "items" in table_names
    assert "inventories" in table_names
    assert "equipment" in table_names
    assert "player_quests" in table_names

    conn.close()
