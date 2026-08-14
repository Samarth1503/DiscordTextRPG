from __future__ import annotations

import discord

from models.enemy import Enemy
from models.equipment import Equipment
from models.player import Player
from utils.formatters import format_gold, format_progress_bar, truncate_text


async def send_response(
    target: discord.abc.Messageable | discord.Interaction,
    embed: discord.Embed,
    view: discord.ui.View | None = None,
) -> None:
    if isinstance(target, discord.Interaction):
        kwargs: dict = {"embed": embed}
        if view is not None:
            kwargs["view"] = view
        else:
            kwargs["view"] = None

        if not target.response.is_done():
            await target.response.edit_message(**kwargs)
        else:
            await target.edit_original_response(**kwargs)
    else:
        kwargs = {"embed": embed}
        if view is not None:
            kwargs["view"] = view
        await target.send(**kwargs)


def success_embed(
    title: str,
    description: str,
) -> discord.Embed:
    return discord.Embed(
        title=truncate_text(f"✅ {title}", 256),
        description=truncate_text(description, 4096),
        color=discord.Color.green(),
    )


def error_embed(
    title: str,
    description: str,
) -> discord.Embed:
    return discord.Embed(
        title=truncate_text(f"❌ {title}", 256),
        description=truncate_text(description, 4096),
        color=discord.Color.red(),
    )


def profile_embed(
    player: Player,
    equipment: Equipment | None = None,
) -> discord.Embed:
    bonuses = equipment.calculate_total_bonus() if equipment else None
    tot_max_hp, tot_atk, tot_def = player.calculate_total_stats(bonuses)

    embed = discord.Embed(
        title=truncate_text(f"⚔️ Character Profile: {player.name}", 256),
        color=discord.Color.blue(),
    )

    embed.add_field(name="Level", value=str(player.level), inline=True)
    embed.add_field(name="XP", value=str(player.experience), inline=True)
    embed.add_field(name="Gold", value=format_gold(player.gold), inline=True)

    hp_bar = format_progress_bar(player.hp, tot_max_hp)
    embed.add_field(
        name=f"❤️ HP ({player.hp}/{tot_max_hp})", value=hp_bar, inline=False
    )

    atk_bonus_str = f" (+{bonuses.attack})" if bonuses and bonuses.attack > 0 else ""
    def_bonus_str = f" (+{bonuses.defense})" if bonuses and bonuses.defense > 0 else ""

    embed.add_field(name="⚔️ Attack", value=f"{tot_atk}{atk_bonus_str}", inline=True)
    embed.add_field(name="🛡️ Defense", value=f"{tot_def}{def_bonus_str}", inline=True)

    if equipment:
        gear_lines = []
        for slot, item in equipment.get_equipped_items().items():
            if item:
                stats_list = []
                if isinstance(item.effect_data, dict):
                    atk = item.effect_data.get("attack", 0)
                    df = item.effect_data.get("defense", 0)
                    hp = item.effect_data.get("hp", 0)
                    if atk:
                        stats_list.append(f"+{atk} Atk")
                    if df:
                        stats_list.append(f"+{df} Def")
                    if hp:
                        stats_list.append(f"+{hp} HP")
                bonus_str = f" ({', '.join(stats_list)})" if stats_list else ""
                gear_lines.append(
                    f"**{slot.value.title()}**: **{item.name}**{bonus_str}"
                )
            else:
                gear_lines.append(f"**{slot.value.title()}**: *Empty*")
        if gear_lines:
            embed.add_field(
                name="🛡️ Equipment", value="\n".join(gear_lines), inline=False
            )

    return embed


def combat_embed(player: Player, enemy: Enemy, combat_log: list[str]) -> discord.Embed:
    embed = discord.Embed(
        title=truncate_text(f"⚔️ Combat: {player.name} vs {enemy.name}", 256),
        color=discord.Color.dark_red(),
    )

    p_bar = format_progress_bar(player.hp, player.max_hp)
    e_bar = format_progress_bar(enemy.hp, enemy.max_hp)

    embed.add_field(name=f"🦸 {player.name} HP", value=p_bar, inline=True)
    embed.add_field(name=f"👹 {enemy.name} HP", value=e_bar, inline=True)

    if combat_log:
        recent_log = "\n".join(combat_log[-4:])
        embed.add_field(
            name="📜 Combat Log", value=truncate_text(recent_log, 1024), inline=False
        )

    return embed
