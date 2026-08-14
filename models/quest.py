from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class QuestObjectiveType(str, Enum):
    KILL_ENEMY = "KILL_ENEMY"
    COLLECT_ITEM = "COLLECT_ITEM"
    REACH_LEVEL = "REACH_LEVEL"
    EARN_GOLD = "EARN_GOLD"


@dataclass(slots=True)
class QuestObjective:
    type: QuestObjectiveType
    target_id: str  # Enemy ID, Item ID, or level/gold target string
    target_amount: int
    description: str

    def __post_init__(self) -> None:
        if self.target_amount <= 0:
            raise ValueError("Target amount must be greater than 0.")
        if not self.description or not self.description.strip():
            raise ValueError("Objective description cannot be empty.")


@dataclass(slots=True)
class QuestReward:
    xp: int = 0
    gold: int = 0
    items: list[tuple[str, int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.xp < 0:
            raise ValueError("Reward XP cannot be negative.")
        if self.gold < 0:
            raise ValueError("Reward gold cannot be negative.")
        for item_id, qty in self.items:
            if not item_id or qty < 1:
                raise ValueError("Invalid item drop reward.")


@dataclass(slots=True)
class Quest:
    id: str
    name: str
    description: str
    required_level: int
    objective: QuestObjective
    reward: QuestReward
    repeatable: bool = False

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Quest ID cannot be empty.")
        if not self.name or not self.name.strip():
            raise ValueError("Quest name cannot be empty.")
        if self.required_level < 1:
            raise ValueError("Required level must be at least 1.")

    def is_complete(self, current_progress: int) -> bool:
        return current_progress >= self.objective.target_amount

    def get_progress_percentage(self, current_progress: int) -> float:
        if current_progress <= 0:
            return 0.0
        return min(100.0, (current_progress / self.objective.target_amount) * 100.0)
