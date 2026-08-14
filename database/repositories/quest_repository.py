from __future__ import annotations

from database.repositories.base_repository import BaseRepository


class QuestRepository(BaseRepository):
    def get_active_quests(self, discord_id: int) -> list[tuple[str, int, str]]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT quest_id, progress, status
                FROM player_quests
                WHERE player_id = ? AND status = 'ACTIVE'
                """,
                (discord_id,),
            ).fetchall()
        finally:
            if self._connection is None:
                conn.close()

        return [(row["quest_id"], row["progress"], row["status"]) for row in rows]

    def get_discovered_quests(self, discord_id: int) -> list[str]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT quest_id
                FROM player_quests
                WHERE player_id = ? AND status = 'DISCOVERED'
                """,
                (discord_id,),
            ).fetchall()
        finally:
            if self._connection is None:
                conn.close()

        return [row["quest_id"] for row in rows]

    def discover_quest(self, discord_id: int, quest_id: str) -> bool:
        conn = self._get_conn()
        try:
            status_data = self.get_quest_status(discord_id, quest_id)
            if status_data is not None:
                return False

            conn.execute(
                """
                INSERT INTO player_quests (player_id, quest_id, progress, status)
                VALUES (?, ?, 0, 'DISCOVERED')
                """,
                (discord_id, quest_id),
            )
            if self._connection is None:
                conn.commit()
            return True
        finally:
            if self._connection is None:
                conn.close()

    def get_quest_status(
        self, discord_id: int, quest_id: str
    ) -> tuple[int, str] | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                """
                SELECT progress, status
                FROM player_quests
                WHERE player_id = ? AND quest_id = ?
                """,
                (discord_id, quest_id),
            ).fetchone()
        finally:
            if self._connection is None:
                conn.close()

        if row is None:
            return None
        return row["progress"], row["status"]

    def assign_quest(self, discord_id: int, quest_id: str) -> None:
        conn = self._get_conn()
        try:
            status_data = self.get_quest_status(discord_id, quest_id)
            if status_data is not None and status_data[1] == "COMPLETED":
                raise ValueError("Quest already completed.")

            conn.execute(
                """
                INSERT INTO player_quests (player_id, quest_id, progress, status)
                VALUES (?, ?, 0, 'ACTIVE')
                ON CONFLICT(player_id, quest_id) DO UPDATE SET
                    status = 'ACTIVE',
                    progress = 0
                """,
                (discord_id, quest_id),
            )
            if self._connection is None:
                conn.commit()
        finally:
            if self._connection is None:
                conn.close()

    def update_progress(self, discord_id: int, quest_id: str, progress: int) -> None:
        if progress < 0:
            raise ValueError("Progress cannot be negative.")

        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """
                UPDATE player_quests
                SET progress = ?
                WHERE player_id = ? AND quest_id = ? AND status = 'ACTIVE'
                """,
                (progress, discord_id, quest_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("Quest is not active for player.")
            if self._connection is None:
                conn.commit()
        finally:
            if self._connection is None:
                conn.close()

    def complete_quest(self, discord_id: int, quest_id: str) -> None:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """
                UPDATE player_quests
                SET status = 'COMPLETED'
                WHERE player_id = ? AND quest_id = ? AND status = 'ACTIVE'
                """,
                (discord_id, quest_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("Quest is not active or already completed.")
            if self._connection is None:
                conn.commit()
        finally:
            if self._connection is None:
                conn.close()

    def fail_quest(self, discord_id: int, quest_id: str) -> None:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """
                UPDATE player_quests
                SET status = 'FAILED'
                WHERE player_id = ? AND quest_id = ? AND status = 'ACTIVE'
                """,
                (discord_id, quest_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("Quest is not active.")
            if self._connection is None:
                conn.commit()
        finally:
            if self._connection is None:
                conn.close()
