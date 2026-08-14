from __future__ import annotations

import discord

from models.player import Player
from utils.action_menu import (
    GameState,
    attach_action_menu,
    determine_game_state,
    format_action_menu,
    get_available_actions,
)


def test_determine_game_state_no_character():
    assert determine_game_state(None) == GameState.NO_CHARACTER


def test_determine_game_state_normal():
    player = Player(discord_id=1, name="Hero")
    assert determine_game_state(player) == GameState.NORMAL


def test_determine_game_state_combat():
    player = Player(discord_id=1, name="Hero")
    assert determine_game_state(player, in_combat=True) == GameState.COMBAT


def test_determine_game_state_dead():
    player = Player(discord_id=1, name="Hero", hp=0)
    assert determine_game_state(player) == GameState.DEAD


def test_get_available_actions_no_character():
    actions = get_available_actions(GameState.NO_CHARACTER)
    cmds = [a[0] for a in actions]
    assert "!start <name>" in cmds
    assert "!explore" not in cmds


def test_get_available_actions_normal():
    actions = get_available_actions(GameState.NORMAL)
    cmds = [a[0] for a in actions]
    assert "!explore" in cmds
    assert "!profile" in cmds
    assert "!inventory" in cmds
    assert "!quests" in cmds
    assert "!shop" in cmds
    assert "!attack" not in cmds


def test_get_available_actions_combat():
    actions = get_available_actions(GameState.COMBAT)
    cmds = [a[0] for a in actions]
    assert "!attack" in cmds
    assert "!flee" in cmds
    assert "!use health_potion" in cmds


def test_get_available_actions_dead():
    actions = get_available_actions(GameState.DEAD)
    cmds = [a[0] for a in actions]
    assert "!rest" in cmds


def test_format_action_menu():
    formatted = format_action_menu(GameState.NORMAL)
    assert "**What would you like to do?**" in formatted
    assert "`!explore`" in formatted


def test_attach_action_menu():
    embed = discord.Embed(title="Test")
    updated = attach_action_menu(embed, GameState.NORMAL)
    field_names = [f.name for f in updated.fields]
    assert "📋 Available Actions" in field_names
