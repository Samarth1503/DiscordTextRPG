from __future__ import annotations

from enum import Enum
import discord

from models.player import Player


class GameState(str, Enum):
    NO_CHARACTER = "NO_CHARACTER"
    NORMAL = "NORMAL"
    COMBAT = "COMBAT"
    DEAD = "DEAD"


def determine_game_state(player: Player | None, in_combat: bool = False) -> GameState:
    if player is None:
        return GameState.NO_CHARACTER
    if not player.is_alive():
        return GameState.DEAD
    if in_combat:
        return GameState.COMBAT
    return GameState.NORMAL


def get_available_actions(
    state: GameState, player: Player | None = None
) -> list[tuple[str, str]]:
    if state == GameState.NO_CHARACTER:
        return [
            ("!start <name>", "Create your character profile"),
            ("!help", "Display bot help and commands"),
        ]
    elif state == GameState.DEAD:
        return [
            ("!rest", "Rest at the tavern for free to restore HP"),
            ("!profile", "View your character stats"),
            ("!inventory", "View your inventory"),
        ]
    elif state == GameState.COMBAT:
        return [
            ("!attack", "Attack your enemy target"),
            ("!use health_potion", "Use a health potion"),
            ("!flee", "Attempt to escape combat"),
            ("!profile", "View your character stats"),
        ]
    else:
        return [
            ("!explore", "Explore the world for monsters, gold & loot"),
            ("!profile", "View your stats & gear"),
            ("!inventory", "View items in your bag"),
            ("!quests", "View quest board missions"),
            ("!shop", "Visit the town merchant"),
            ("!rest", "Rest at the tavern to recover HP"),
        ]


def format_action_menu(state: GameState, player: Player | None = None) -> str:
    actions = get_available_actions(state, player)
    lines = ["**What would you like to do?**"]
    for command, description in actions:
        lines.append(f"• `{command}` — {description}")
    return "\n".join(lines)


def attach_action_menu(
    embed: discord.Embed, state: GameState, player: Player | None = None
) -> discord.Embed:
    menu_text = format_action_menu(state, player)
    embed.add_field(name="📋 Available Actions", value=menu_text, inline=False)
    return embed
