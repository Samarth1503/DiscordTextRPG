from __future__ import annotations

import pytest

from game.combat import execute_turn
from models.equipment import EquipmentSlot
from models.player import Player
from ui.views import MainMenuView, PostBuyEquipView


def test_execute_turn_with_effective_stats(sample_player, sample_enemy):
    init_hp = sample_enemy.hp
    # Turn with base attack
    res_base = execute_turn(
        sample_player, sample_enemy, action="attack", effective_attack=10
    )
    base_dmg = res_base.player_damage_dealt

    # Reset enemy hp
    sample_enemy.hp = init_hp
    # Turn with boosted effective attack
    res_boosted = execute_turn(
        sample_player, sample_enemy, action="attack", effective_attack=50
    )
    boosted_dmg = res_boosted.player_damage_dealt

    assert boosted_dmg > base_dmg


def test_equipment_equip_unequip_roundtrip(uow):
    player = Player(discord_id=8888, name="GearHero")
    with uow:
        uow.players.create(player)

        # Add sword to inventory
        uow.inventories.add_item(8888, "iron_sword", 1)
        assert uow.inventories.has_item(8888, "iron_sword", 1)

        # Equip sword
        prev_item = uow.equipment.equip_item(8888, EquipmentSlot.WEAPON, "iron_sword")
        assert prev_item is None

        # Check equipment repository
        equipped = uow.equipment.get_equipped_items(8888)
        assert equipped[EquipmentSlot.WEAPON] == "iron_sword"

        # Unequip weapon
        unequipped_id = uow.equipment.unequip_slot(8888, EquipmentSlot.WEAPON)
        assert unequipped_id == "iron_sword"

        equipped_after = uow.equipment.get_equipped_items(8888)
        assert equipped_after.get(EquipmentSlot.WEAPON) is None


def test_main_menu_view_attributes():
    # Mock bot
    class DummyBot:
        pass

    view = MainMenuView(DummyBot(), player_id=12345)
    assert len(view.children) == 7
    labels = [button.label for button in view.children]
    assert "Explore 🗺️" in labels
    assert "Profile 📊" in labels
    assert "Inventory 🎒" in labels
    assert "Quests 📜" in labels
    assert "Shop 🏪" in labels
    assert "Rest 🛌" in labels
    assert "Check All Commands 📖" in labels


def test_post_buy_equip_view_attributes():
    class DummyBot:
        pass

    view = PostBuyEquipView(
        DummyBot(), player_id=12345, item_id="iron_sword", item_name="Iron Sword"
    )
    assert len(view.children) == 2
    labels = [button.label for button in view.children]
    assert "Equip Now 🛡️" in labels
    assert "Continue Shopping 🏪" in labels


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_send_response_interaction():
    from unittest.mock import AsyncMock, MagicMock
    import discord
    from utils.embeds import send_response

    mock_interaction = MagicMock(spec=discord.Interaction)
    mock_interaction.response = MagicMock()
    mock_interaction.response.is_done.return_value = False
    mock_interaction.response.edit_message = AsyncMock()

    embed = discord.Embed(title="Test")
    await send_response(mock_interaction, embed=embed)

    mock_interaction.response.edit_message.assert_awaited_once()
