from __future__ import annotations

import sqlite3
from typing import Generic, TypeVar

from database.connection import get_connection

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, connection: sqlite3.Connection | None = None) -> None:
        self._connection = connection

    def _get_conn(self) -> sqlite3.Connection:
        if self._connection is not None:
            return self._connection
        return get_connection()
