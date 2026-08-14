from __future__ import annotations

import sqlite3
from typing import Self

from database.connection import get_connection
from database.repositories.player_repository import PlayerRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.equipment_repository import EquipmentRepository
from database.repositories.quest_repository import QuestRepository


class UnitOfWork:
    def __init__(self, connection: sqlite3.Connection | None = None) -> None:
        self._external_conn = connection is not None
        self.connection = connection if connection else get_connection()
        self._in_transaction = False

        self.players = PlayerRepository(self.connection)
        self.inventories = InventoryRepository(self.connection)
        self.equipment = EquipmentRepository(self.connection)
        self.quests = QuestRepository(self.connection)

    def __enter__(self) -> Self:
        if self._in_transaction:
            raise RuntimeError("Transaction already active")
        self.connection.execute("BEGIN IMMEDIATE;")
        self._in_transaction = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()
        finally:
            self._in_transaction = False
            if not self._external_conn:
                self.connection.close()

    def commit(self) -> None:
        if self._in_transaction:
            self.connection.commit()
            self._in_transaction = False

    def rollback(self) -> None:
        if self._in_transaction:
            self.connection.rollback()
            self._in_transaction = False
