from __future__ import annotations

from database.connection import get_connection
from database.schema_initializer import initialize_schema


def test_schema_migration_idempotency(tmp_path):
    db_file = tmp_path / "mig.db"
    conn = get_connection(str(db_file))

    # Apply initial schema
    initialize_schema(conn)

    # Re-apply schema 3 times to verify idempotency
    initialize_schema(conn)
    initialize_schema(conn)
    initialize_schema(conn)

    indices = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index';"
    ).fetchall()
    idx_names = [i["name"] for i in indices]

    assert "idx_inventories_player" in idx_names
    assert "idx_equipment_player" in idx_names
    assert "idx_player_quests_player" in idx_names

    conn.close()
