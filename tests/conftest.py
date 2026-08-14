from __future__ import annotations

import pytest

import database.connection as connection_module
from database.repositories.player_repository import PlayerRepository
from database.schema_initializer import initialize_schema
from database.unit_of_work import UnitOfWork
from models.enemy import Enemy, LootDrop
from models.item import Item, ItemRarity, ItemType
from models.player import Player


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    database_dir = tmp_path / "storage"
    database_path = database_dir / "test.db"

    monkeypatch.setattr(connection_module, "DATABASE_DIR", database_dir)
    monkeypatch.setattr(connection_module, "DATABASE_PATH", database_path)

    initialize_schema()
    return database_path


@pytest.fixture
def repository(db_path) -> PlayerRepository:
    return PlayerRepository()


@pytest.fixture
def uow(db_path) -> UnitOfWork:
    return UnitOfWork()


@pytest.fixture
def sample_player() -> Player:
    return Player(
        discord_id=123456789,
        name="TestHero",
        level=1,
        experience=0,
        hp=100,
        max_hp=100,
        attack=10,
        defense=5,
        gold=100,
    )


@pytest.fixture
def sample_enemy() -> Enemy:
    return Enemy(
        id="goblin_test",
        name="Test Goblin",
        level=1,
        hp=30,
        max_hp=30,
        attack=8,
        defense=2,
        xp_reward=20,
        gold_reward=15,
        loot_table=[
            LootDrop(
                item_id="health_potion", drop_chance=1.0, min_quantity=1, max_quantity=1
            ),
        ],
    )


@pytest.fixture
def sample_item() -> Item:
    return Item(
        id="health_potion",
        name="Health Potion",
        description="Restores 50 HP",
        type=ItemType.CONSUMABLE,
        rarity=ItemRarity.COMMON,
        buy_price=20,
        sell_price=10,
        stackable=True,
        max_stack=99,
        effect_data={"heal_hp": 50},
    )
