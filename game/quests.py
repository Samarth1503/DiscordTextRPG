from __future__ import annotations

import time
from dataclasses import dataclass

from models.quest import Quest


@dataclass(slots=True)
class QuestSelectionContext:
    discord_id: int
    quests: list[Quest]
    created_at: float
    timeout_seconds: float = 60.0

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.timeout_seconds

    def get_quest_by_number(self, number: int) -> Quest | None:
        if self.is_expired():
            return None
        if 1 <= number <= len(self.quests):
            return self.quests[number - 1]
        return None


class QuestSelectionStore:
    def __init__(self) -> None:
        self._store: dict[int, QuestSelectionContext] = {}

    def set_selection(
        self, discord_id: int, quests: list[Quest], timeout: float = 60.0
    ) -> QuestSelectionContext:
        ctx = QuestSelectionContext(
            discord_id=discord_id,
            quests=quests,
            created_at=time.time(),
            timeout_seconds=timeout,
        )
        self._store[discord_id] = ctx
        return ctx

    def get_selection(self, discord_id: int) -> QuestSelectionContext | None:
        ctx = self._store.get(discord_id)
        if ctx is None:
            return None
        if ctx.is_expired():
            self._store.pop(discord_id, None)
            return None
        return ctx

    def clear_selection(self, discord_id: int) -> None:
        self._store.pop(discord_id, None)


quest_selection_store = QuestSelectionStore()
