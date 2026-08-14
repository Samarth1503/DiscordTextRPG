from __future__ import annotations

from models.quest import Quest, QuestObjective, QuestObjectiveType, QuestReward

QUEST_REGISTRY: dict[str, Quest] = {
    "first_steps": Quest(
        id="first_steps",
        name="First Steps",
        description="Defeat your first enemy in combat to prove your valour.",
        required_level=1,
        objective=QuestObjective(
            type=QuestObjectiveType.KILL_ENEMY,
            target_id="goblin",
            target_amount=1,
            description="Defeat 1 Scout Goblin",
        ),
        reward=QuestReward(
            xp=50,
            gold=30,
            items=[("health_potion", 2)],
        ),
        repeatable=False,
    ),
    "goblin_slayer": Quest(
        id="goblin_slayer",
        name="Goblin Menace",
        description="Clear out the goblin scouts threatening the village.",
        required_level=1,
        objective=QuestObjective(
            type=QuestObjectiveType.KILL_ENEMY,
            target_id="goblin",
            target_amount=5,
            description="Defeat 5 Scout Goblins",
        ),
        reward=QuestReward(
            xp=150,
            gold=100,
            items=[("wooden_sword", 1)],
        ),
        repeatable=True,
    ),
    "wolf_hunter": Quest(
        id="wolf_hunter",
        name="Wolf Pack Hunt",
        description="Thin out the Dire Wolf pack roaming the forest.",
        required_level=2,
        objective=QuestObjective(
            type=QuestObjectiveType.KILL_ENEMY,
            target_id="wolf",
            target_amount=3,
            description="Defeat 3 Dire Wolves",
        ),
        reward=QuestReward(
            xp=200,
            gold=150,
            items=[("leather_armor", 1)],
        ),
        repeatable=False,
    ),
    "skeleton_purifier": Quest(
        id="skeleton_purifier",
        name="Crypt Cleansing",
        description="Purify the crypt by destroying skeleton warriors.",
        required_level=2,
        objective=QuestObjective(
            type=QuestObjectiveType.KILL_ENEMY,
            target_id="skeleton",
            target_amount=3,
            description="Defeat 3 Skeletons",
        ),
        reward=QuestReward(
            xp=220,
            gold=160,
            items=[("iron_sword", 1)],
        ),
        repeatable=False,
    ),
    "herb_collector": Quest(
        id="herb_collector",
        name="Alchemist Supplies",
        description="Stock up on essential health potions for the town doctor.",
        required_level=1,
        objective=QuestObjective(
            type=QuestObjectiveType.COLLECT_ITEM,
            target_id="health_potion",
            target_amount=3,
            description="Collect 3 Health Potions",
        ),
        reward=QuestReward(
            xp=100,
            gold=80,
        ),
        repeatable=True,
    ),
    "wealthy_adventurer": Quest(
        id="wealthy_adventurer",
        name="Merchant's Fortune",
        description="Accumulate wealth through combat and exploration.",
        required_level=2,
        objective=QuestObjective(
            type=QuestObjectiveType.EARN_GOLD,
            target_id="gold",
            target_amount=200,
            description="Earn 200 Gold",
        ),
        reward=QuestReward(
            xp=250,
            gold=100,
        ),
        repeatable=False,
    ),
    "veteran_hero": Quest(
        id="veteran_hero",
        name="Veteran's Ascension",
        description="Prove your strength by leveling up your character.",
        required_level=3,
        objective=QuestObjective(
            type=QuestObjectiveType.REACH_LEVEL,
            target_id="level",
            target_amount=3,
            description="Reach Character Level 3",
        ),
        reward=QuestReward(
            xp=300,
            gold=250,
            items=[("chainmail_armor", 1)],
        ),
        repeatable=False,
    ),
    "lost_caravan": Quest(
        id="lost_caravan",
        name="The Lost Caravan",
        description="A travelling merchant lost goods to wolves along the trade route.",
        required_level=1,
        objective=QuestObjective(
            type=QuestObjectiveType.KILL_ENEMY,
            target_id="wolf",
            target_amount=3,
            description="Defeat 3 Forest Wolves",
        ),
        reward=QuestReward(
            xp=180,
            gold=120,
            items=[("iron_dagger", 1)],
        ),
        repeatable=False,
    ),
    "merchant_supply": Quest(
        id="merchant_supply",
        name="Merchant Supply Run",
        description="Deliver pelt materials to the traveling merchant.",
        required_level=2,
        objective=QuestObjective(
            type=QuestObjectiveType.COLLECT_ITEM,
            target_id="wolf_pelt",
            target_amount=3,
            description="Collect 3 Wolf Pelts",
        ),
        reward=QuestReward(
            xp=200,
            gold=150,
        ),
        repeatable=False,
    ),
}


def get_quest(quest_id: str) -> Quest:
    if quest_id not in QUEST_REGISTRY:
        raise KeyError(f"Quest ID '{quest_id}' not found in registry.")
    return QUEST_REGISTRY[quest_id]


def get_available_quests(player_level: int) -> list[Quest]:
    return [q for q in QUEST_REGISTRY.values() if q.required_level <= player_level]
