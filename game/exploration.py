from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from models.player import Player


class ExplorationEventType(str, Enum):
    ENCOUNTER_ENEMY = "ENCOUNTER_ENEMY"
    FIND_GOLD = "FIND_GOLD"
    FIND_ITEM = "FIND_ITEM"
    QUEST_EVENT = "QUEST_EVENT"
    RARE_EVENT = "RARE_EVENT"


@dataclass(slots=True)
class ExplorationOutcome:
    event_type: ExplorationEventType
    description: str
    enemy_id: str | None = None
    gold_amount: int = 0
    item_id: str | None = None
    item_quantity: int = 0


EVENT_WEIGHTS = [
    (ExplorationEventType.ENCOUNTER_ENEMY, 0.40),
    (ExplorationEventType.FIND_GOLD, 0.25),
    (ExplorationEventType.FIND_ITEM, 0.20),
    (ExplorationEventType.QUEST_EVENT, 0.10),
    (ExplorationEventType.RARE_EVENT, 0.05),
]


def roll_exploration_event(player: Player) -> ExplorationOutcome:
    if not player.is_alive():
        raise ValueError("Player must be alive to explore.")

    roll = random.random()
    cumulative = 0.0
    selected_event = ExplorationEventType.ENCOUNTER_ENEMY

    for event_type, weight in EVENT_WEIGHTS:
        cumulative += weight
        if roll <= cumulative:
            selected_event = event_type
            break

    if selected_event == ExplorationEventType.ENCOUNTER_ENEMY:
        enemies = ["goblin", "wolf", "skeleton"]
        chosen = random.choice(enemies)
        return ExplorationOutcome(
            event_type=selected_event,
            description=f"A wild **{chosen.title()}** appears from the shadows!",
            enemy_id=chosen,
        )

    elif selected_event == ExplorationEventType.FIND_GOLD:
        found_gold = random.randint(10, 30) * player.level
        return ExplorationOutcome(
            event_type=selected_event,
            description=f"You found a hidden pouch containing **{found_gold}** gold coins!",
            gold_amount=found_gold,
        )

    elif selected_event == ExplorationEventType.FIND_ITEM:
        items = ["health_potion", "leather_armor", "wooden_sword"]
        chosen_item = random.choice(items)
        return ExplorationOutcome(
            event_type=selected_event,
            description=f"You stumbled upon an abandoned chest and found **1x {chosen_item.replace('_', ' ').title()}**!",
            item_id=chosen_item,
            item_quantity=1,
        )

    elif selected_event == ExplorationEventType.QUEST_EVENT:
        return ExplorationOutcome(
            event_type=selected_event,
            description="You met a travelling merchant with news of a new quest assignment!",
        )

    else:  # RARE_EVENT
        found_gold = random.randint(100, 250) * player.level
        return ExplorationOutcome(
            event_type=selected_event,
            description=f"✨ **RARE EVENT!** You discovered an ancient glowing shrine and were blessed with **{found_gold}** gold!",
            gold_amount=found_gold,
        )
