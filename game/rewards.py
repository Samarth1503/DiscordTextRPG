from __future__ import annotations

from dataclasses import dataclass, field

from game.leveling import add_experience
from models.player import Player


@dataclass(slots=True)
class RewardSummary:
    xp_gained: int
    gold_gained: int
    levels_gained: int
    new_level: int
    drops: list[tuple[str, int]] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


def apply_rewards(
    player: Player,
    xp: int,
    gold: int,
    drops: list[tuple[str, int]] | None = None,
) -> RewardSummary:
    if xp < 0 or gold < 0:
        raise ValueError("Rewards cannot be negative.")

    drops = drops or []
    messages: list[str] = []

    old_level = player.level
    new_xp, new_lvl = add_experience(player.experience, xp)
    levels_gained = new_lvl - old_level

    player.experience = new_xp
    player.level = new_lvl
    player.gold += gold

    if xp > 0:
        messages.append(f"✨ Gained **+{xp} XP**!")
    if gold > 0:
        messages.append(f"🪙 Gained **+{gold} Gold**!")

    if levels_gained > 0:
        # Increase player stats on level up
        hp_boost = 10 * levels_gained
        atk_boost = 2 * levels_gained
        def_boost = 1 * levels_gained

        player.max_hp += hp_boost
        player.hp = player.max_hp  # Fully heal on level up
        player.attack += atk_boost
        player.defense += def_boost

        messages.append(
            f"🎉 **LEVEL UP!** You reached **Level {new_lvl}**!\n"
            f"Stat Increases: **+{hp_boost} Max HP**, **+{atk_boost} Atk**, **+{def_boost} Def**!"
        )

    for item_id, qty in drops:
        messages.append(
            f"📦 Received item: **{qty}x {item_id.replace('_', ' ').title()}**!"
        )

    return RewardSummary(
        xp_gained=xp,
        gold_gained=gold,
        levels_gained=levels_gained,
        new_level=new_lvl,
        drops=drops,
        messages=messages,
    )
