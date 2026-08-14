from __future__ import annotations

import random
from models.enemy import Enemy, LootDrop

ENEMY_REGISTRY: dict[str, Enemy] = {
    "slime": Enemy(
        id="slime",
        name="Forest Slime",
        level=1,
        hp=25,
        max_hp=25,
        attack=6,
        defense=1,
        xp_reward=20,
        gold_reward=10,
        loot_table=[
            LootDrop(
                item_id="health_potion", drop_chance=0.5, min_quantity=1, max_quantity=1
            ),
        ],
    ),
    "goblin": Enemy(
        id="goblin",
        name="Scout Goblin",
        level=1,
        hp=35,
        max_hp=35,
        attack=8,
        defense=2,
        xp_reward=25,
        gold_reward=15,
        loot_table=[
            LootDrop(
                item_id="goblin_ear", drop_chance=0.8, min_quantity=1, max_quantity=2
            ),
            LootDrop(
                item_id="health_potion", drop_chance=0.4, min_quantity=1, max_quantity=1
            ),
        ],
    ),
    "wolf": Enemy(
        id="wolf",
        name="Dire Wolf",
        level=2,
        hp=50,
        max_hp=50,
        attack=12,
        defense=3,
        xp_reward=45,
        gold_reward=25,
        loot_table=[
            LootDrop(
                item_id="wolf_pelt", drop_chance=0.7, min_quantity=1, max_quantity=1
            ),
        ],
    ),
    "skeleton": Enemy(
        id="skeleton",
        name="Skeleton Warrior",
        level=3,
        hp=75,
        max_hp=75,
        attack=16,
        defense=5,
        xp_reward=70,
        gold_reward=40,
        loot_table=[
            LootDrop(
                item_id="wooden_sword", drop_chance=0.2, min_quantity=1, max_quantity=1
            ),
            LootDrop(
                item_id="health_potion", drop_chance=0.5, min_quantity=1, max_quantity=2
            ),
        ],
    ),
    "orc_warrior": Enemy(
        id="orc_warrior",
        name="Orc Brute",
        level=5,
        hp=120,
        max_hp=120,
        attack=24,
        defense=8,
        xp_reward=130,
        gold_reward=80,
        loot_table=[
            LootDrop(
                item_id="iron_sword", drop_chance=0.25, min_quantity=1, max_quantity=1
            ),
            LootDrop(
                item_id="chainmail_armor",
                drop_chance=0.15,
                min_quantity=1,
                max_quantity=1,
            ),
        ],
    ),
}


def get_enemy(enemy_id: str) -> Enemy:
    if enemy_id not in ENEMY_REGISTRY:
        raise KeyError(f"Enemy ID '{enemy_id}' not found in registry.")

    template = ENEMY_REGISTRY[enemy_id]
    return Enemy(
        id=template.id,
        name=template.name,
        level=template.level,
        hp=template.max_hp,
        max_hp=template.max_hp,
        attack=template.attack,
        defense=template.defense,
        xp_reward=template.xp_reward,
        gold_reward=template.gold_reward,
        loot_table=template.loot_table,
    )


def get_random_enemy_for_level(player_level: int) -> Enemy:
    # Strictly filter enemies appropriate for player's level
    suitable = [e for e in ENEMY_REGISTRY.values() if e.level <= player_level]
    if not suitable:
        suitable = [e for e in ENEMY_REGISTRY.values() if e.level == 1]

    chosen = random.choice(suitable)
    return get_enemy(chosen.id)
