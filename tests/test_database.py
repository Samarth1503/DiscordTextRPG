from __future__ import annotations

import sqlite3

import pytest

import database.connection as connection_module
from database.repositories.player_repository import PlayerRepository
from database.schema_initializer import initialize_schema
from models.player import Player


@pytest.fixture
def database(tmp_path, monkeypatch):
    database_dir = tmp_path / "storage"
    database_path = database_dir / "test.db"

    monkeypatch.setattr(
        connection_module,
        "DATABASE_DIR",
        database_dir,
    )
    monkeypatch.setattr(
        connection_module,
        "DATABASE_PATH",
        database_path,
    )

    initialize_schema()

    return database_path


@pytest.fixture
def repository(database):
    return PlayerRepository()


def test_database_schema_is_created(database):
    assert database.exists()

    with sqlite3.connect(database) as connection:
        table = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'players'
            """).fetchone()

    assert table is not None


def test_create_and_get_player(repository):
    player = Player(
        discord_id=123456789,
        name="Arthur",
    )

    repository.create(player)

    result = repository.get_by_discord_id(123456789)

    assert result == player


def test_get_missing_player_returns_none(repository):
    result = repository.get_by_discord_id(999999999)

    assert result is None


def test_duplicate_player_is_rejected(repository):
    player = Player(
        discord_id=123456789,
        name="Arthur",
    )

    repository.create(player)

    with pytest.raises(ValueError):
        repository.create(player)


def test_update_player(repository):
    player = Player(
        discord_id=123456789,
        name="Arthur",
    )

    repository.create(player)

    player.level = 2
    player.experience = 100
    player.hp = 120
    player.max_hp = 120
    player.attack = 15
    player.defense = 8
    player.gold = 250

    repository.update(player)

    result = repository.get_by_discord_id(123456789)

    assert result == player


def test_update_missing_player_is_rejected(repository):
    player = Player(
        discord_id=123456789,
        name="Arthur",
    )

    with pytest.raises(ValueError):
        repository.update(player)


def test_invalid_player_state_is_rejected(repository):
    with pytest.raises(ValueError):
        player = Player(
            discord_id=123456789,
            name="Arthur",
            level=0,
        )
        repository.create(player)


def test_empty_player_name_is_rejected(repository):
    with pytest.raises(ValueError):
        player = Player(
            discord_id=123456789,
            name="   ",
        )
        repository.create(player)


def test_negative_gold_is_rejected(repository):
    with pytest.raises(ValueError):
        player = Player(
            discord_id=123456789,
            name="Arthur",
            gold=-100,
        )
        repository.create(player)


def test_hp_cannot_exceed_max_hp(repository):
    with pytest.raises(ValueError):
        player = Player(
            discord_id=123456789,
            name="Arthur",
            hp=150,
            max_hp=100,
        )
        repository.create(player)
