from __future__ import annotations

import sqlite3

from database.repositories.base_repository import BaseRepository
from models.player import Player


class PlayerRepository(BaseRepository[Player]):
    def get_by_discord_id(self, discord_id: int) -> Player | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                """
                SELECT
                    discord_id,
                    name,
                    level,
                    experience,
                    hp,
                    max_hp,
                    attack,
                    defense,
                    gold
                FROM players
                WHERE discord_id = ?
                """,
                (discord_id,),
            ).fetchone()
        finally:
            if self._connection is None:
                conn.close()

        if row is None:
            return None

        return self._row_to_player(row)

    def create(self, player: Player) -> Player:
        conn = self._get_conn()
        try:
            conn.execute(
                """
                INSERT INTO players (
                    discord_id,
                    name,
                    level,
                    experience,
                    hp,
                    max_hp,
                    attack,
                    defense,
                    gold
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    player.discord_id,
                    player.name,
                    player.level,
                    player.experience,
                    player.hp,
                    player.max_hp,
                    player.attack,
                    player.defense,
                    player.gold,
                ),
            )
            if self._connection is None:
                conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("Player already exists or contains invalid data.") from exc
        finally:
            if self._connection is None:
                conn.close()

        return player

    def update(self, player: Player) -> None:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """
                UPDATE players
                SET
                    name = ?,
                    level = ?,
                    experience = ?,
                    hp = ?,
                    max_hp = ?,
                    attack = ?,
                    defense = ?,
                    gold = ?
                WHERE discord_id = ?
                """,
                (
                    player.name,
                    player.level,
                    player.experience,
                    player.hp,
                    player.max_hp,
                    player.attack,
                    player.defense,
                    player.gold,
                    player.discord_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("Player does not exist.")
            if self._connection is None:
                conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("Invalid player state for update.") from exc
        finally:
            if self._connection is None:
                conn.close()

    def delete(self, discord_id: int) -> bool:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM players WHERE discord_id = ?",
                (discord_id,),
            )
            if self._connection is None:
                conn.commit()
            return cursor.rowcount > 0
        finally:
            if self._connection is None:
                conn.close()

    def get_top_players_by_level(self, limit: int = 10) -> list[Player]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT
                    discord_id, name, level, experience, hp, max_hp, attack, defense, gold
                FROM players
                ORDER BY level DESC, experience DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            if self._connection is None:
                conn.close()

        return [self._row_to_player(row) for row in rows]

    @staticmethod
    def _row_to_player(row: sqlite3.Row) -> Player:
        return Player(
            discord_id=row["discord_id"],
            name=row["name"],
            level=row["level"],
            experience=row["experience"],
            hp=row["hp"],
            max_hp=row["max_hp"],
            attack=row["attack"],
            defense=row["defense"],
            gold=row["gold"],
        )
