from __future__ import annotations

import discord
from discord.ext import commands

from data.enemies import get_enemy, get_random_enemy_for_level
from data.quests import get_available_quests, get_quest
from database.unit_of_work import UnitOfWork
from game.quests import quest_selection_store
from game.rewards import apply_rewards
from models.quest import QuestObjectiveType
from ui.views import MainMenuView
from utils.checks import has_character
from utils.embeds import error_embed, send_response, success_embed


class QuestsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def do_quests(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        user: discord.User | discord.Member,
    ) -> None:
        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(user.id)
            active = uow.quests.get_active_quests(user.id)

        if player is None:
            await send_response(
                target,
                embed=error_embed(
                    "No Character",
                    "You don't have a character yet! Use `!start <name>`.",
                ),
            )
            return

        all_available = get_available_quests(player.level)

        filtered_available = []
        with UnitOfWork() as uow:
            for q_obj in all_available:
                status_data = uow.quests.get_quest_status(user.id, q_obj.id)
                if status_data is not None:
                    _, status = status_data
                    if status == "ACTIVE":
                        continue
                    if status == "COMPLETED" and not q_obj.repeatable:
                        continue
                filtered_available.append(q_obj)

        embed = discord.Embed(
            title="📜 Quest Board",
            color=discord.Color.gold(),
        )

        active_lines = []
        for q_id, prog, status in active:
            try:
                q_obj = get_quest(q_id)
                pct = q_obj.get_progress_percentage(prog)
                active_lines.append(
                    f"• **{q_obj.name}**: {prog}/{q_obj.objective.target_amount} ({int(pct)}%) — *{q_obj.objective.description}*"
                )
            except KeyError:
                active_lines.append(f"• `{q_id}`: {prog}")

        embed.add_field(
            name="⚔️ Active Quests",
            value=(
                "\n".join(active_lines)
                if active_lines
                else "*No active quests. Accept one below!*"
            ),
            inline=False,
        )

        avail_lines = []
        for index, q_obj in enumerate(filtered_available, 1):
            avail_lines.append(
                f"**{index}. {q_obj.name}**\n"
                f"   *{q_obj.description}*\n"
                f"   Objective: {q_obj.objective.description}\n"
                f"   Reward: ⭐ {q_obj.reward.xp} XP • 🪙 {q_obj.reward.gold} Gold"
            )

        if filtered_available:
            quest_selection_store.set_selection(
                user.id, filtered_available, timeout=60.0
            )
            avail_value = (
                "\n\n".join(avail_lines)
                + "\n\n👉 **Choose a quest by typing `!accept <quest_number>`.**"
            )
        else:
            quest_selection_store.clear_selection(user.id)
            avail_value = "*No available quests for your level.*"

        embed.add_field(
            name="📋 Available Quests",
            value=avail_value,
            inline=False,
        )

        await send_response(target, embed=embed, view=MainMenuView(self.bot, user.id))

    async def execute_accept_quest(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        user: discord.User | discord.Member,
        quest_identifier: str,
    ) -> None:
        quest_identifier = quest_identifier.strip()
        q_obj = None

        try:
            num = int(quest_identifier)
            is_num = True
        except ValueError:
            is_num = False

        if is_num:
            if num <= 0:
                await send_response(
                    target,
                    embed=error_embed(
                        "Invalid Selection",
                        "Quest number must be 1 or greater.",
                    ),
                )
                return
            sel_ctx = quest_selection_store.get_selection(user.id)
            if sel_ctx is not None:
                q_obj = sel_ctx.get_quest_by_number(num)
            if q_obj is None:
                await send_response(
                    target,
                    embed=error_embed(
                        "Invalid Selection",
                        f"Invalid quest number `{num}`. Type `!quests` to view available quests.",
                    ),
                )
                return
        else:
            try:
                q_obj = get_quest(quest_identifier.lower())
            except KeyError:
                await send_response(
                    target,
                    embed=error_embed(
                        "Quest Not Found",
                        f"Unknown quest `{quest_identifier}`.",
                    ),
                )
                return

        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(user.id)
            if player is None:
                await send_response(
                    target,
                    embed=error_embed(
                        "No Character",
                        "You don't have a character yet! Use `!start <name>`.",
                    ),
                )
                return

            if player.level < q_obj.required_level:
                await send_response(
                    target,
                    embed=error_embed(
                        "Level Required",
                        f"You must be at least **Level {q_obj.required_level}** to accept **{q_obj.name}**.",
                    ),
                )
                return

            status_data = uow.quests.get_quest_status(user.id, q_obj.id)
            if status_data is not None:
                prog, status = status_data
                if status == "ACTIVE":
                    await send_response(
                        target,
                        embed=error_embed(
                            "Quest Already Active",
                            f"You already have **{q_obj.name}** active!",
                        ),
                    )
                    return
                elif status == "COMPLETED" and not q_obj.repeatable:
                    await send_response(
                        target,
                        embed=error_embed(
                            "Quest Completed",
                            f"You have already completed **{q_obj.name}**!",
                        ),
                    )
                    return

            try:
                uow.quests.assign_quest(user.id, q_obj.id)
            except ValueError as exc:
                await send_response(
                    target,
                    embed=error_embed(
                        "Cannot Accept Quest",
                        str(exc),
                    ),
                )
                return

        quest_selection_store.clear_selection(user.id)

        reward_lines = []
        if q_obj.reward.xp > 0:
            reward_lines.append(f"⭐ **{q_obj.reward.xp} XP**")
        if q_obj.reward.gold > 0:
            reward_lines.append(f"🪙 **{q_obj.reward.gold} Gold**")
        for item_id, qty in q_obj.reward.items:
            reward_lines.append(f"📦 **{qty}x {item_id}**")

        reward_text = "\n".join(reward_lines) if reward_lines else "None"

        embed = success_embed(
            "Quest Accepted",
            f"📜 Accepted quest: **{q_obj.name}**\n\n"
            f"**Objective:**\n{q_obj.objective.description}\n\n"
            f"**Rewards:**\n{reward_text}\n\n"
            f"⚔️ **Battle Starting Immediately!** Preparing your encounter...",
        )
        await send_response(target, embed=embed, view=MainMenuView(self.bot, user.id))

        if q_obj.objective.type == QuestObjectiveType.KILL_ENEMY:
            combat_cog = self.bot.get_cog("CombatCog")
            if combat_cog:
                try:
                    enemy = get_enemy(q_obj.objective.target_id)
                except KeyError:
                    enemy = get_random_enemy_for_level(player.level)
                await combat_cog.start_encounter(
                    target, user, enemy, source="quest", quest_id=q_obj.id
                )

    @commands.command(name="quests", aliases=["quest"])
    @has_character()
    async def quests(self, ctx: commands.Context) -> None:
        await self.do_quests(ctx.channel, ctx.author)

    @commands.command(name="accept")
    @has_character()
    async def accept(self, ctx: commands.Context, selection: str = "") -> None:
        if not selection or not selection.strip():
            await send_response(
                ctx.channel,
                embed=error_embed(
                    "Missing Quest Number",
                    "Please specify a quest number to accept.\nExample: `!accept 1`",
                ),
            )
            return
        await self.execute_accept_quest(ctx.channel, ctx.author, selection)

    @commands.command(name="claim")
    @has_character()
    async def claim(self, ctx: commands.Context, quest_id: str) -> None:
        quest_id = quest_id.strip().lower()

        try:
            q_obj = get_quest(quest_id)
        except KeyError:
            await ctx.send(
                embed=error_embed(
                    "Quest Not Found",
                    f"Unknown quest `{quest_id}`.",
                )
            )
            return

        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(ctx.author.id)
            status_data = uow.quests.get_quest_status(ctx.author.id, quest_id)

            if player is None or status_data is None:
                await ctx.send(
                    embed=error_embed(
                        "Quest Not Active",
                        "You have not accepted this quest.",
                    )
                )
                return

            prog, status = status_data
            if status != "ACTIVE":
                await ctx.send(
                    embed=error_embed(
                        "Quest Completed",
                        "You have already claimed this quest reward.",
                    )
                )
                return

            if not q_obj.is_complete(prog):
                await ctx.send(
                    embed=error_embed(
                        "Objective Incomplete",
                        f"Objective not complete! Progress: **{prog}/{q_obj.objective.target_amount}**.",
                    )
                )
                return

            uow.quests.complete_quest(ctx.author.id, quest_id)
            for item_id, qty in q_obj.reward.items:
                uow.inventories.add_item(ctx.author.id, item_id, qty)

            summary = apply_rewards(
                player,
                xp=q_obj.reward.xp,
                gold=q_obj.reward.gold,
                drops=q_obj.reward.items,
            )
            uow.players.update(player)

        embed = success_embed(
            "Quest Claimed!",
            f"🎉 Completed **{q_obj.name}**!\n\n" + "\n".join(summary.messages),
        )
        await ctx.send(embed=embed, view=MainMenuView(self.bot, ctx.author.id))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(QuestsCog(bot))
