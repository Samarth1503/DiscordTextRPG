from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from models.item import Item, ItemType


class EquipmentSlot(str, Enum):
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    ACCESSORY_1 = "ACCESSORY_1"
    ACCESSORY_2 = "ACCESSORY_2"


@dataclass(slots=True)
class StatBonus:
    attack: int = 0
    defense: int = 0
    hp: int = 0

    def add(self, other: StatBonus) -> StatBonus:
        return StatBonus(
            attack=self.attack + other.attack,
            defense=self.defense + other.defense,
            hp=self.hp + other.hp,
        )


@dataclass(slots=True)
class Equipment:
    weapon: Item | None = None
    armor: Item | None = None
    accessory_1: Item | None = None
    accessory_2: Item | None = None

    def __post_init__(self) -> None:
        self.validate_slot(self.weapon, EquipmentSlot.WEAPON)
        self.validate_slot(self.armor, EquipmentSlot.ARMOR)
        self.validate_slot(self.accessory_1, EquipmentSlot.ACCESSORY_1)
        self.validate_slot(self.accessory_2, EquipmentSlot.ACCESSORY_2)

    @staticmethod
    def validate_slot(item: Item | None, slot: EquipmentSlot) -> None:
        if item is None:
            return
        if slot == EquipmentSlot.WEAPON and item.type != ItemType.WEAPON:
            raise TypeError(
                f"Item '{item.name}' of type {item.type} cannot be equipped in WEAPON slot."
            )
        if slot == EquipmentSlot.ARMOR and item.type != ItemType.ARMOR:
            raise TypeError(
                f"Item '{item.name}' of type {item.type} cannot be equipped in ARMOR slot."
            )
        if slot in (
            EquipmentSlot.ACCESSORY_1,
            EquipmentSlot.ACCESSORY_2,
        ) and item.type not in (ItemType.ACCESSORY, ItemType.MISC):
            raise TypeError(
                f"Item '{item.name}' of type {item.type} cannot be equipped in ACCESSORY slot."
            )

    def get_equipped_items(self) -> dict[EquipmentSlot, Item]:
        equipped = {}
        if self.weapon:
            equipped[EquipmentSlot.WEAPON] = self.weapon
        if self.armor:
            equipped[EquipmentSlot.ARMOR] = self.armor
        if self.accessory_1:
            equipped[EquipmentSlot.ACCESSORY_1] = self.accessory_1
        if self.accessory_2:
            equipped[EquipmentSlot.ACCESSORY_2] = self.accessory_2
        return equipped

    def calculate_total_bonus(self) -> StatBonus:
        total = StatBonus()
        for item in (self.weapon, self.armor, self.accessory_1, self.accessory_2):
            if item is not None and isinstance(item.effect_data, dict):
                bonus = StatBonus(
                    attack=item.effect_data.get("attack", 0),
                    defense=item.effect_data.get("defense", 0),
                    hp=item.effect_data.get("hp", 0),
                )
                total = total.add(bonus)
        return total
