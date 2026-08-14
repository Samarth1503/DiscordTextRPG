from __future__ import annotations

from database.repositories.base_repository import BaseRepository


class InventoryRepository(BaseRepository):
    def get_inventory(self, discord_id: int) -> list[tuple[str, int]]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT item_id, quantity
                FROM inventories
                WHERE player_id = ?
                ORDER BY item_id ASC
                """,
                (discord_id,),
            ).fetchall()
        finally:
            if self._connection is None:
                conn.close()

        return [(row["item_id"], row["quantity"]) for row in rows]

    def has_item(self, discord_id: int, item_id: str, quantity: int = 1) -> bool:
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")
        conn = self._get_conn()
        try:
            row = conn.execute(
                """
                SELECT quantity FROM inventories
                WHERE player_id = ? AND item_id = ?
                """,
                (discord_id, item_id),
            ).fetchone()
        finally:
            if self._connection is None:
                conn.close()

        return row is not None and row["quantity"] >= quantity

    def get_item_quantity(self, discord_id: int, item_id: str) -> int:
        conn = self._get_conn()
        try:
            row = conn.execute(
                """
                SELECT quantity FROM inventories
                WHERE player_id = ? AND item_id = ?
                """,
                (discord_id, item_id),
            ).fetchone()
        finally:
            if self._connection is None:
                conn.close()

        return row["quantity"] if row else 0

    def add_item(self, discord_id: int, item_id: str, quantity: int = 1) -> None:
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")

        conn = self._get_conn()
        try:
            conn.execute(
                """
                INSERT INTO inventories (player_id, item_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(player_id, item_id) DO UPDATE SET
                    quantity = quantity + excluded.quantity
                """,
                (discord_id, item_id, quantity),
            )
            if self._connection is None:
                conn.commit()
        finally:
            if self._connection is None:
                conn.close()

    def remove_item(self, discord_id: int, item_id: str, quantity: int = 1) -> None:
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")

        conn = self._get_conn()
        try:
            row = conn.execute(
                """
                SELECT quantity FROM inventories
                WHERE player_id = ? AND item_id = ?
                """,
                (discord_id, item_id),
            ).fetchone()

            if row is None or row["quantity"] < quantity:
                raise ValueError("Insufficient item quantity in inventory.")

            current_qty = row["quantity"]
            if current_qty == quantity:
                conn.execute(
                    "DELETE FROM inventories WHERE player_id = ? AND item_id = ?",
                    (discord_id, item_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE inventories
                    SET quantity = quantity - ?
                    WHERE player_id = ? AND item_id = ?
                    """,
                    (quantity, discord_id, item_id),
                )

            if self._connection is None:
                conn.commit()
        finally:
            if self._connection is None:
                conn.close()
