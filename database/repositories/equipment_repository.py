from __future__ import annotations

from database.repositories.base_repository import BaseRepository
from models.equipment import EquipmentSlot


class EquipmentRepository(BaseRepository):
    VALID_SLOTS = {
        EquipmentSlot.WEAPON: "weapon_id",
        EquipmentSlot.ARMOR: "armor_id",
        EquipmentSlot.ACCESSORY_1: "accessory_1_id",
        EquipmentSlot.ACCESSORY_2: "accessory_2_id",
    }

    def get_equipped_items(self, discord_id: int) -> dict[EquipmentSlot, str | None]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                """
                SELECT weapon_id, armor_id, accessory_1_id, accessory_2_id
                FROM equipment
                WHERE player_id = ?
                """,
                (discord_id,),
            ).fetchone()
        finally:
            if self._connection is None:
                conn.close()

        if row is None:
            return {
                EquipmentSlot.WEAPON: None,
                EquipmentSlot.ARMOR: None,
                EquipmentSlot.ACCESSORY_1: None,
                EquipmentSlot.ACCESSORY_2: None,
            }

        return {
            EquipmentSlot.WEAPON: row["weapon_id"],
            EquipmentSlot.ARMOR: row["armor_id"],
            EquipmentSlot.ACCESSORY_1: row["accessory_1_id"],
            EquipmentSlot.ACCESSORY_2: row["accessory_2_id"],
        }

    def equip_item(
        self, discord_id: int, slot: EquipmentSlot, item_id: str
    ) -> str | None:
        if slot not in self.VALID_SLOTS:
            raise ValueError(f"Invalid equipment slot '{slot}'.")

        column_name = self.VALID_SLOTS[slot]
        conn = self._get_conn()
        try:
            row = conn.execute(
                f"SELECT {column_name} FROM equipment WHERE player_id = ?",
                (discord_id,),
            ).fetchone()

            previous_item = row[column_name] if row else None

            conn.execute(
                f"""
                INSERT INTO equipment (player_id, {column_name})
                VALUES (?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    {column_name} = excluded.{column_name}
                """,
                (discord_id, item_id),
            )

            if self._connection is None:
                conn.commit()
        finally:
            if self._connection is None:
                conn.close()

        return previous_item

    def unequip_slot(self, discord_id: int, slot: EquipmentSlot) -> str | None:
        if slot not in self.VALID_SLOTS:
            raise ValueError(f"Invalid equipment slot '{slot}'.")

        column_name = self.VALID_SLOTS[slot]
        conn = self._get_conn()
        try:
            row = conn.execute(
                f"SELECT {column_name} FROM equipment WHERE player_id = ?",
                (discord_id,),
            ).fetchone()

            if row is None or row[column_name] is None:
                return None

            previous_item = row[column_name]
            conn.execute(
                f"UPDATE equipment SET {column_name} = NULL WHERE player_id = ?",
                (discord_id,),
            )

            if self._connection is None:
                conn.commit()
        finally:
            if self._connection is None:
                conn.close()

        return previous_item
