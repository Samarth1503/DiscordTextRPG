from __future__ import annotations

import json
import sqlite3
from database.connection import get_connection


def initialize_schema(conn: sqlite3.Connection | None = None) -> None:
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        with conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS players (
                discord_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                experience INTEGER NOT NULL DEFAULT 0,
                hp INTEGER NOT NULL DEFAULT 100,
                max_hp INTEGER NOT NULL DEFAULT 100,
                attack INTEGER NOT NULL DEFAULT 10,
                defense INTEGER NOT NULL DEFAULT 5,
                gold INTEGER NOT NULL DEFAULT 0,
                CHECK (length(trim(name)) > 0),
                CHECK (level >= 1),
                CHECK (experience >= 0),
                CHECK (hp >= 0),
                CHECK (max_hp > 0),
                CHECK (hp <= max_hp),
                CHECK (attack >= 0),
                CHECK (defense >= 0),
                CHECK (gold >= 0)
            );

            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                type TEXT NOT NULL,
                rarity TEXT NOT NULL DEFAULT 'COMMON',
                buy_price INTEGER NOT NULL DEFAULT 0,
                sell_price INTEGER NOT NULL DEFAULT 0,
                stackable INTEGER NOT NULL DEFAULT 1,
                max_stack INTEGER NOT NULL DEFAULT 99,
                effect_data TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS inventories (
                player_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (player_id, item_id),
                FOREIGN KEY (player_id) REFERENCES players(discord_id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                CHECK (quantity >= 1)
            );

            CREATE TABLE IF NOT EXISTS equipment (
                player_id INTEGER PRIMARY KEY,
                weapon_id TEXT,
                armor_id TEXT,
                accessory_1_id TEXT,
                accessory_2_id TEXT,
                FOREIGN KEY (player_id) REFERENCES players(discord_id) ON DELETE CASCADE,
                FOREIGN KEY (weapon_id) REFERENCES items(id) ON DELETE SET NULL,
                FOREIGN KEY (armor_id) REFERENCES items(id) ON DELETE SET NULL,
                FOREIGN KEY (accessory_1_id) REFERENCES items(id) ON DELETE SET NULL,
                FOREIGN KEY (accessory_2_id) REFERENCES items(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS player_quests (
                player_id INTEGER NOT NULL,
                quest_id TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                PRIMARY KEY (player_id, quest_id),
                FOREIGN KEY (player_id) REFERENCES players(discord_id) ON DELETE CASCADE,
                CHECK (progress >= 0),
                CHECK (status IN ('DISCOVERED', 'ACTIVE', 'COMPLETED', 'FAILED'))
            );

            CREATE INDEX IF NOT EXISTS idx_inventories_player ON inventories(player_id);
            CREATE INDEX IF NOT EXISTS idx_equipment_player ON equipment(player_id);
            CREATE INDEX IF NOT EXISTS idx_player_quests_player ON player_quests(player_id);
            """)

            cursor = conn.execute("PRAGMA table_info(player_quests)")
            columns = cursor.fetchall()
            if columns:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS player_quests_new (
                    player_id INTEGER NOT NULL,
                    quest_id TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    PRIMARY KEY (player_id, quest_id),
                    FOREIGN KEY (player_id) REFERENCES players(discord_id) ON DELETE CASCADE,
                    CHECK (progress >= 0),
                    CHECK (status IN ('DISCOVERED', 'ACTIVE', 'COMPLETED', 'FAILED'))
                );
                """)
                conn.execute("""
                INSERT OR IGNORE INTO player_quests_new (player_id, quest_id, progress, status)
                SELECT player_id, quest_id, progress, status FROM player_quests;
                """)
                conn.execute("DROP TABLE IF EXISTS player_quests;")
                conn.execute("ALTER TABLE player_quests_new RENAME TO player_quests;")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_player_quests_player ON player_quests(player_id);"
                )

            from data.items import get_all_items

            for item in get_all_items():
                conn.execute(
                    """
                    INSERT INTO items (
                        id, name, description, type, rarity,
                        buy_price, sell_price, stackable, max_stack, effect_data
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        description = excluded.description,
                        type = excluded.type,
                        rarity = excluded.rarity,
                        buy_price = excluded.buy_price,
                        sell_price = excluded.sell_price,
                        stackable = excluded.stackable,
                        max_stack = excluded.max_stack,
                        effect_data = excluded.effect_data
                    """,
                    (
                        item.id,
                        item.name,
                        item.description,
                        (
                            item.type.value
                            if hasattr(item.type, "value")
                            else str(item.type)
                        ),
                        (
                            item.rarity.value
                            if hasattr(item.rarity, "value")
                            else str(item.rarity)
                        ),
                        item.buy_price,
                        item.sell_price,
                        1 if item.stackable else 0,
                        item.max_stack,
                        json.dumps(item.effect_data),
                    ),
                )
    finally:
        if should_close:
            conn.close()
