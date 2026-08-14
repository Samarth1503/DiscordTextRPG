from __future__ import annotations

import pytest
import discord
from unittest.mock import AsyncMock, MagicMock

from data.items import get_item
from data.quests import QUEST_REGISTRY
from models.equipment import Equipment, EquipmentSlot
from models.player import Player
from ui.views import MainMenuView, CommandReferenceView


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ==================================================
# GOAL 1 — QUEST EXPANSION & MERCHANT DISCOVERY
# ==================================================


def test_quest_catalog_expanded():
    assert "skeleton_purifier" in QUEST_REGISTRY
    assert "herb_collector" in QUEST_REGISTRY
    assert "wealthy_adventurer" in QUEST_REGISTRY
    assert "veteran_hero" in QUEST_REGISTRY
    assert "lost_caravan" in QUEST_REGISTRY
    assert "merchant_supply" in QUEST_REGISTRY

    for q_id, q in QUEST_REGISTRY.items():
        assert q.id == q_id
        assert q.name and q.name.strip()
        assert q.description and q.description.strip()
        assert q.required_level >= 1
        assert q.objective.target_amount > 0
        assert q.reward.xp >= 0
        assert q.reward.gold >= 0


def test_quest_discovery_repository(uow):
    player = Player(discord_id=7777, name="QuestSeeker")
    with uow:
        uow.players.create(player)

        discovered = uow.quests.get_discovered_quests(7777)
        assert len(discovered) == 0

        # Discover quest
        res1 = uow.quests.discover_quest(7777, "lost_caravan")
        assert res1 is True

        discovered_after = uow.quests.get_discovered_quests(7777)
        assert "lost_caravan" in discovered_after

        # Duplicate discovery should return False
        res2 = uow.quests.discover_quest(7777, "lost_caravan")
        assert res2 is False


def test_merchant_quest_no_duplicate(uow):
    player = Player(discord_id=7778, name="MerchantHero")
    with uow:
        uow.players.create(player)
        uow.quests.discover_quest(7778, "lost_caravan")
        uow.quests.assign_quest(7778, "lost_caravan")

        status_data = uow.quests.get_quest_status(7778, "lost_caravan")
        assert status_data is not None
        assert status_data[1] == "ACTIVE"

        # Discovering again should not alter status
        res = uow.quests.discover_quest(7778, "lost_caravan")
        assert res is False


# ==================================================
# GOAL 2 — NEW SHOP EQUIPMENT
# ==================================================


def test_new_equipment_catalog():
    new_items = [
        "iron_dagger",
        "steel_sword",
        "iron_helmet",
        "steel_chestplate",
        "leather_boots",
        "iron_greaves",
        "ring_of_strength",
        "amulet_of_protection",
    ]
    for item_id in new_items:
        item = get_item(item_id)
        assert item.id == item_id
        assert item.buy_price > 0
        assert item.sell_price > 0
        assert item.sell_price <= item.buy_price


def test_equip_new_armor_and_accessories(uow):
    player = Player(discord_id=9999, name="ArmorKnight")
    with uow:
        uow.players.create(player)
        uow.inventories.add_item(9999, "iron_helmet", 1)
        uow.inventories.add_item(9999, "ring_of_strength", 1)

        # Equip helmet
        prev_helm = uow.equipment.equip_item(9999, EquipmentSlot.ARMOR, "iron_helmet")
        assert prev_helm is None

        # Equip ring
        prev_ring = uow.equipment.equip_item(
            9999, EquipmentSlot.ACCESSORY_1, "ring_of_strength"
        )
        assert prev_ring is None

        equipped = uow.equipment.get_equipped_items(9999)
        assert equipped[EquipmentSlot.ARMOR] == "iron_helmet"
        assert equipped[EquipmentSlot.ACCESSORY_1] == "ring_of_strength"

        # Calculate bonuses
        eq = Equipment()
        eq.armor = get_item("iron_helmet")
        eq.accessory_1 = get_item("ring_of_strength")
        bonuses = eq.calculate_total_bonus()
        assert bonuses.defense == 3
        assert bonuses.attack == 5

        _, eff_atk, eff_def = player.calculate_total_stats(bonuses)
        assert eff_atk == player.attack + 5
        assert eff_def == player.defense + 3


# ==================================================
# GOAL 3 — COMMAND REFERENCE
# ==================================================


def test_main_menu_view_has_commands_button():
    class DummyBot:
        pass

    view = MainMenuView(DummyBot(), player_id=123)
    labels = [btn.label for btn in view.children if isinstance(btn, discord.ui.Button)]
    assert "Check All Commands 📖" in labels


def test_command_reference_view():
    class DummyBot:
        pass

    view = CommandReferenceView(DummyBot(), player_id=123)
    labels = [btn.label for btn in view.children if isinstance(btn, discord.ui.Button)]
    assert "Back 🔙" in labels


@pytest.mark.anyio
async def test_do_commands_embed_output():
    from cogs.general import GeneralCog

    bot = MagicMock()
    cog = GeneralCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 123

    await cog.do_commands(target, user)
    target.response.edit_message.assert_awaited_once()

    _, kwargs = target.response.edit_message.call_args
    embed = kwargs.get("embed")
    assert embed is not None
    assert "Command Reference" in embed.title
    field_names = [f.name for f in embed.fields]
    assert "👤 Character" in field_names
    assert "🗺️ Adventure" in field_names
    assert "⚔️ Combat" in field_names
    assert "🎒 Inventory & Equipment" in field_names
    assert "🏪 Merchant Shop" in field_names
    assert "📜 Quests" in field_names


# ==================================================
# GOAL 4 — QUEST ACCEPTANCE INSTRUCTIONS & VALIDATION
# ==================================================


@pytest.mark.anyio
async def test_quest_acceptance_validation_invalid_number():
    from cogs.quests import QuestsCog

    bot = MagicMock()
    cog = QuestsCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 5555

    # Test negative number
    await cog.execute_accept_quest(target, user, "-1")
    target.response.edit_message.assert_awaited()
    _, kwargs = target.response.edit_message.call_args
    embed = kwargs.get("embed")
    assert "Invalid Selection" in embed.title

    # Test zero
    await cog.execute_accept_quest(target, user, "0")
    _, kwargs = target.response.edit_message.call_args
    embed = kwargs.get("embed")
    assert "Invalid Selection" in embed.title

    # Test out-of-range number
    await cog.execute_accept_quest(target, user, "999999")
    _, kwargs = target.response.edit_message.call_args
    embed = kwargs.get("embed")
    assert "Invalid Selection" in embed.title
