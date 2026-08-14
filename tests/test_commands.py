from __future__ import annotations

import pytest
from database.unit_of_work import UnitOfWork
from models.player import Player
from utils.action_menu import GameState, determine_game_state, get_available_actions


def test_player_start_success(db_path):
    with UnitOfWork() as uow:
        player = Player(discord_id=999111, name="Knight")
        uow.players.create(player)
        uow.inventories.add_item(999111, "health_potion", 2)

    with UnitOfWork() as uow:
        fetched = uow.players.get_by_discord_id(999111)
        assert fetched is not None
        assert fetched.name == "Knight"
        assert uow.inventories.has_item(999111, "health_potion", 2)


def test_duplicate_character_rejected(db_path):
    with UnitOfWork() as uow:
        player = Player(discord_id=999222, name="Mage")
        uow.players.create(player)

    with pytest.raises(ValueError):
        with UnitOfWork() as uow:
            uow.players.create(Player(discord_id=999222, name="Mage2"))


def test_empty_character_name_rejected():
    with pytest.raises(ValueError, match="Player name cannot be empty"):
        Player(discord_id=1, name="   ")


def test_long_character_name_rejected():
    long_name = "A" * 33
    with pytest.raises(ValueError):
        if len(long_name) > 32:
            raise ValueError("Character name cannot exceed 32 characters.")


def test_no_character_menu_options():
    actions = get_available_actions(GameState.NO_CHARACTER)
    cmds = [a[0] for a in actions]
    assert "!start <name>" in cmds
    assert "!explore" not in cmds


def test_normal_character_menu_options():
    p = Player(discord_id=1, name="Hero")
    state = determine_game_state(p)
    actions = get_available_actions(state)
    cmds = [a[0] for a in actions]
    assert "!explore" in cmds
    assert "!profile" in cmds


def test_dead_player_menu_options():
    p = Player(discord_id=1, name="Hero", hp=0)
    state = determine_game_state(p)
    assert state == GameState.DEAD
    actions = get_available_actions(state)
    cmds = [a[0] for a in actions]
    assert "!rest" in cmds
    assert "!explore" not in cmds


def test_combat_menu_options():
    p = Player(discord_id=1, name="Hero")
    state = determine_game_state(p, in_combat=True)
    assert state == GameState.COMBAT
    actions = get_available_actions(state)
    cmds = [a[0] for a in actions]
    assert "!attack" in cmds
    assert "!flee" in cmds
    assert "!explore" not in cmds
