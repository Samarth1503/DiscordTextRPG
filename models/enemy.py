from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass(slots=True)
class LootDrop:
    item_id: str
    drop_chance: float  # 0.0 to 1.0
    min_quantity: int = 1
    max_quantity: int = 1

    def __post_init__(self) -> None:
        if not self.item_id or not self.item_id.strip():
            raise ValueError("Item ID cannot be empty.")
        if not (0.0 <= self.drop_chance <= 1.0):
            raise ValueError("Drop chance must be between 0.0 and 1.0.")
        if self.min_quantity < 1 or self.max_quantity < self.min_quantity:
            raise ValueError("Invalid drop quantity range.")


@dataclass(slots=True)
class Enemy:
    id: str
    name: str
    level: int
    hp: int
    max_hp: int
    attack: int
    defense: int
    xp_reward: int
    gold_reward: int
    loot_table: list[LootDrop] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Enemy ID cannot be empty.")
        if not self.name or not self.name.strip():
            raise ValueError("Enemy name cannot be empty.")
        if self.level < 1:
            raise ValueError("Enemy level must be at least 1.")
        if self.max_hp <= 0:
            raise ValueError("Enemy Max HP must be greater than 0.")
        if self.hp < 0 or self.hp > self.max_hp:
            raise ValueError("Enemy HP must be between 0 and Max HP.")
        if self.attack < 0:
            raise ValueError("Enemy Attack cannot be negative.")
        if self.defense < 0:
            raise ValueError("Enemy Defense cannot be negative.")
        if self.xp_reward < 0:
            raise ValueError("XP reward cannot be negative.")
        if self.gold_reward < 0:
            raise ValueError("Gold reward cannot be negative.")

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("Damage amount cannot be negative.")
        actual_damage = min(self.hp, amount)
        self.hp -= actual_damage
        return actual_damage

    def roll_loot(self) -> list[tuple[str, int]]:
        drops: list[tuple[str, int]] = []
        for loot in self.loot_table:
            if random.random() <= loot.drop_chance:
                qty = random.randint(loot.min_quantity, loot.max_quantity)
                drops.append((loot.item_id, qty))
        return drops
