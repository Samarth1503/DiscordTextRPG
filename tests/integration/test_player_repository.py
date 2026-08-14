from __future__ import annotations

from database.unit_of_work import UnitOfWork
from models.equipment import EquipmentSlot
from models.player import Player


def test_unit_of_work_transaction_commit(db_path):
    with UnitOfWork() as uow:
        player = Player(discord_id=101, name="Knight")
        uow.players.create(player)

    with UnitOfWork() as uow:
        fetched = uow.players.get_by_discord_id(101)
        assert fetched is not None
        assert fetched.name == "Knight"


def test_unit_of_work_rollback_on_exception(db_path):
    try:
        with UnitOfWork() as uow:
            player = Player(discord_id=102, name="Mage")
            uow.players.create(player)
            raise RuntimeError("Simulated transaction failure")
    except RuntimeError:
        pass

    with UnitOfWork() as uow:
        fetched = uow.players.get_by_discord_id(102)
        assert fetched is None


def test_inventory_and_equipment_repository(db_path):
    with UnitOfWork() as uow:
        player = Player(discord_id=103, name="Paladin")
        uow.players.create(player)

        uow.connection.execute("""
            INSERT OR REPLACE INTO items (id, name, description, type, buy_price, sell_price)
            VALUES ('iron_sword', 'Iron Sword', 'Sword', 'WEAPON', 100, 50)
            """)

        uow.inventories.add_item(103, "iron_sword", 1)
        assert uow.inventories.has_item(103, "iron_sword", 1)

        uow.equipment.equip_item(103, EquipmentSlot.WEAPON, "iron_sword")
        eq = uow.equipment.get_equipped_items(103)
        assert eq[EquipmentSlot.WEAPON] == "iron_sword"


def test_quest_repository_flow(db_path):
    with UnitOfWork() as uow:
        player = Player(discord_id=104, name="Archer")
        uow.players.create(player)

        uow.quests.assign_quest(104, "first_steps")
        active = uow.quests.get_active_quests(104)
        assert len(active) == 1
        assert active[0][0] == "first_steps"

        uow.quests.update_progress(104, "first_steps", 1)
        uow.quests.complete_quest(104, "first_steps")

        status_data = uow.quests.get_quest_status(104, "first_steps")
        assert status_data == (1, "COMPLETED")
