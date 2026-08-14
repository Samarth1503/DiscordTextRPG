from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ItemType(str, Enum):
    CONSUMABLE = "CONSUMABLE"
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    ACCESSORY = "ACCESSORY"
    QUEST = "QUEST"
    MISC = "MISC"


class ItemRarity(str, Enum):
    COMMON = "COMMON"
    UNCOMMON = "UNCOMMON"
    RARE = "RARE"
    EPIC = "EPIC"
    LEGENDARY = "LEGENDARY"


@dataclass(slots=True)
class Item:
    id: str
    name: str
    description: str
    type: ItemType
    rarity: ItemRarity = ItemRarity.COMMON
    buy_price: int = 10
    sell_price: int = 5
    stackable: bool = True
    max_stack: int = 99
    effect_data: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Item ID cannot be empty.")
        if not self.name or not self.name.strip():
            raise ValueError("Item name cannot be empty.")
        if self.buy_price < 0:
            raise ValueError("Buy price cannot be negative.")
        if self.sell_price < 0:
            raise ValueError("Sell price cannot be negative.")
        if self.sell_price > self.buy_price:
            raise ValueError("Sell price cannot exceed buy price.")
        if self.max_stack < 1:
            raise ValueError("Max stack must be at least 1.")
