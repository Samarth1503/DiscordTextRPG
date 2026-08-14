from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.equipment import StatBonus


@dataclass(slots=True)
class Player:
    discord_id: int
    name: str
    level: int = 1
    experience: int = 0
    hp: int = 100
    max_hp: int = 100
    attack: int = 10
    defense: int = 5
    gold: int = 0

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Player name cannot be empty.")
        if self.level < 1:
            raise ValueError("Player level must be at least 1.")
        if self.experience < 0:
            raise ValueError("Experience cannot be negative.")
        if self.max_hp <= 0:
            raise ValueError("Max HP must be greater than 0.")
        if self.hp < 0 or self.hp > self.max_hp:
            raise ValueError("HP must be between 0 and Max HP.")
        if self.attack < 0:
            raise ValueError("Attack cannot be negative.")
        if self.defense < 0:
            raise ValueError("Defense cannot be negative.")
        if self.gold < 0:
            raise ValueError("Gold cannot be negative.")

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("Damage amount cannot be negative.")
        actual_damage = min(self.hp, amount)
        self.hp -= actual_damage
        return actual_damage

    def heal(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("Heal amount cannot be negative.")
        missing_hp = self.max_hp - self.hp
        actual_heal = min(missing_hp, amount)
        self.hp += actual_heal
        return actual_heal

    def can_afford(self, cost: int) -> bool:
        if cost < 0:
            raise ValueError("Cost cannot be negative.")
        return self.gold >= cost

    def calculate_total_stats(
        self, equipment_bonuses: StatBonus | None = None
    ) -> tuple[int, int, int]:
        """Returns effective (max_hp, attack, defense) including equipment bonuses."""
        if equipment_bonuses is None:
            return self.max_hp, self.attack, self.defense

        total_max_hp = self.max_hp + equipment_bonuses.hp
        total_attack = self.attack + equipment_bonuses.attack
        total_defense = self.defense + equipment_bonuses.defense
        return max(1, total_max_hp), max(0, total_attack), max(0, total_defense)
