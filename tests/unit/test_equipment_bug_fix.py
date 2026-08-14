from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import discord
import pytest

from data.items import get_item
from database.unit_of_work import UnitOfWork
from models.equipment import Equipment, EquipmentSlot
from models.player import Player
from ui.views import MainMenuView, PostBuyEquipView
from cogs.inventory import InventoryCog
from cogs.shop import ShopCog


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ==================================================
# PASS TEST CASES
# ==================================================


def test_pass_1_owning_equipment_does_not_auto_equip_or_change_stats(db_path):
    player = Player(discord_id=3001, name="RingOwner", attack=10, defense=5)
    with UnitOfWork() as uow:
        uow.players.create(player)
        uow.inventories.add_item(3001, "ring_of_strength", 3)

    with UnitOfWork() as fresh_uow:
        p = fresh_uow.players.get_by_discord_id(3001)
        eq_dict = fresh_uow.equipment.get_equipped_items(3001)

        # 1. Not automatically equipped
        assert eq_dict[EquipmentSlot.ACCESSORY_1] is None
        assert eq_dict[EquipmentSlot.ACCESSORY_2] is None

        # 2. Stats unchanged (effective stats equal base stats)
        eq = Equipment()
        tot_hp, tot_atk, tot_def = p.calculate_total_stats(eq.calculate_total_bonus())
        assert tot_atk == 10
        assert tot_def == 5
        assert p.attack == 10


@pytest.mark.anyio
async def test_pass_2_3_equip_and_unequip_ring_of_strength(db_path):
    player = Player(discord_id=3002, name="RingWearer", attack=10, defense=5)
    with UnitOfWork() as uow:
        uow.players.create(player)
        uow.inventories.add_item(3002, "ring_of_strength", 1)

    bot = MagicMock()
    inv_cog = InventoryCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 3002

    # 1. Equip ring_of_strength
    await inv_cog.do_equip(target, user, "ring_of_strength")

    with UnitOfWork() as fresh_uow:
        p = fresh_uow.players.get_by_discord_id(3002)
        eq_dict = fresh_uow.equipment.get_equipped_items(3002)
        assert eq_dict[EquipmentSlot.ACCESSORY_1] == "ring_of_strength"

        # Calculate effective stats
        eq = Equipment(accessory_1=get_item("ring_of_strength"))
        tot_hp, tot_atk, tot_def = p.calculate_total_stats(eq.calculate_total_bonus())
        assert tot_atk == 15  # 10 base + 5 ring
        assert p.attack == 10  # Base attack remains 10!

    # 2. Unequip ring_of_strength
    ctx = AsyncMock()
    ctx.author = user

    await inv_cog.unequip.callback(inv_cog, ctx, "accessory_1")

    with UnitOfWork() as fresh_uow:
        p_after = fresh_uow.players.get_by_discord_id(3002)
        eq_dict_after = fresh_uow.equipment.get_equipped_items(3002)
        assert eq_dict_after[EquipmentSlot.ACCESSORY_1] is None

        eq_empty = Equipment()
        _, tot_atk_after, _ = p_after.calculate_total_stats(
            eq_empty.calculate_total_bonus()
        )
        assert tot_atk_after == 10  # Returned to base 10


@pytest.mark.anyio
async def test_pass_4_equip_two_rings_from_three_owned(db_path):
    player = Player(discord_id=3004, name="MultiRing", attack=10)
    with UnitOfWork() as uow:
        uow.players.create(player)
        uow.inventories.add_item(3004, "ring_of_strength", 3)

    bot = MagicMock()
    inv_cog = InventoryCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 3004

    # Equip 1st ring -> ACCESSORY_1
    await inv_cog.do_equip(target, user, "ring_of_strength")
    # Equip 2nd ring -> ACCESSORY_2
    await inv_cog.do_equip(target, user, "ring_of_strength")

    with UnitOfWork() as fresh_uow:
        eq_dict = fresh_uow.equipment.get_equipped_items(3004)
        assert eq_dict[EquipmentSlot.ACCESSORY_1] == "ring_of_strength"
        assert eq_dict[EquipmentSlot.ACCESSORY_2] == "ring_of_strength"

        # Check effective attack: 10 + 5 + 5 = 20
        p = fresh_uow.players.get_by_discord_id(3004)
        ring_item = get_item("ring_of_strength")
        eq = Equipment(accessory_1=ring_item, accessory_2=ring_item)
        _, tot_atk, _ = p.calculate_total_stats(eq.calculate_total_bonus())
        assert tot_atk == 20


@pytest.mark.anyio
async def test_pass_5_equip_unowned_item_fails(db_path):
    player = Player(discord_id=3005, name="NoGear")
    with UnitOfWork() as uow:
        uow.players.create(player)

    bot = MagicMock()
    inv_cog = InventoryCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 3005

    await inv_cog.do_equip(target, user, "iron_sword")

    with UnitOfWork() as fresh_uow:
        eq_dict = fresh_uow.equipment.get_equipped_items(3005)
        assert eq_dict[EquipmentSlot.WEAPON] is None


@pytest.mark.anyio
async def test_pass_8_9_equipment_persistence_across_reloads(db_path):
    player = Player(discord_id=3008, name="PersistPlayer", attack=10)
    with UnitOfWork() as uow:
        uow.players.create(player)
        uow.inventories.add_item(3008, "ring_of_strength", 1)
        uow.equipment.equip_item(3008, EquipmentSlot.ACCESSORY_1, "ring_of_strength")
        uow.inventories.remove_item(3008, "ring_of_strength", 1)

    # Reload database fresh
    with UnitOfWork() as fresh_uow:
        eq_dict = fresh_uow.equipment.get_equipped_items(3008)
        assert eq_dict[EquipmentSlot.ACCESSORY_1] == "ring_of_strength"

        fresh_uow.equipment.unequip_slot(3008, EquipmentSlot.ACCESSORY_1)
        fresh_uow.inventories.add_item(3008, "ring_of_strength", 1)

    with UnitOfWork() as fresh_uow2:
        eq_dict_after = fresh_uow2.equipment.get_equipped_items(3008)
        assert eq_dict_after[EquipmentSlot.ACCESSORY_1] is None


@pytest.mark.anyio
async def test_pass_10_shop_purchase_sends_equip_instructions(db_path):
    player = Player(discord_id=3010, name="Buyer", gold=500)
    with UnitOfWork() as uow:
        uow.players.create(player)

    bot = MagicMock()
    shop_cog = ShopCog(bot)

    ctx = AsyncMock()
    ctx.author = MagicMock()
    ctx.author.id = 3010
    ctx.send = AsyncMock()

    await shop_cog.buy.callback(shop_cog, ctx, "ring_of_strength", 1)

    ctx.send.assert_awaited_once()
    _, kwargs = ctx.send.call_args
    embed = kwargs.get("embed")
    view = kwargs.get("view")

    assert embed is not None
    assert "Purchase Successful" in embed.title
    assert "To equip it" in embed.description
    assert isinstance(view, PostBuyEquipView)


@pytest.mark.anyio
async def test_pass_12_button_security_rejects_other_users():
    bot = MagicMock()
    view = MainMenuView(bot, player_id=4000)

    other_user_interaction = AsyncMock(spec=discord.Interaction)
    other_user_interaction.user = MagicMock()
    other_user_interaction.user.id = 9999  # Unauthorized!
    other_user_interaction.response = MagicMock()
    other_user_interaction.response.send_message = AsyncMock()

    res = await view.interaction_check(other_user_interaction)
    assert res is False
    other_user_interaction.response.send_message.assert_awaited_once_with(
        "This is not your action menu!", ephemeral=True
    )


# ==================================================
# FAIL TEST CASES
# ==================================================


@pytest.mark.anyio
async def test_fail_12_prevent_selling_currently_equipped_gear(db_path):
    player = Player(discord_id=5012, name="EquippedSeller", gold=100)
    with UnitOfWork() as uow:
        uow.players.create(player)
        uow.inventories.add_item(5012, "iron_sword", 1)
        uow.equipment.equip_item(5012, EquipmentSlot.WEAPON, "iron_sword")

    bot = MagicMock()
    shop_cog = ShopCog(bot)

    ctx = AsyncMock()
    ctx.author = MagicMock()
    ctx.author.id = 5012
    ctx.send = AsyncMock()

    # Attempt to sell 1x iron_sword which is currently equipped
    await shop_cog.sell.callback(shop_cog, ctx, "iron_sword", 1)

    ctx.send.assert_awaited_once()
    _, kwargs = ctx.send.call_args
    embed = kwargs.get("embed")
    assert embed is not None
    assert "Cannot Sell Equipped Item" in embed.title

    with UnitOfWork() as fresh_uow:
        eq_dict = fresh_uow.equipment.get_equipped_items(5012)
        assert eq_dict[EquipmentSlot.WEAPON] == "iron_sword"
