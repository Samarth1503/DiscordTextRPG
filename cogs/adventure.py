from __future__ import annotations

import discord
from discord.ext import commands

from data.enemies import get_random_enemy_for_level
from database.unit_of_work import UnitOfWork
from game.exploration import ExplorationEventType, roll_exploration_event
from game.rewards import apply_rewards
from ui.views import DeadPlayerView, MainMenuView
from utils.checks import is_alive
from utils.embeds import error_embed, send_response, success_embed


class AdventureCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def do_explore(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        user: discord.User | discord.Member,
    ) -> None:
        combat_cog = self.bot.get_cog("CombatCog")
        if combat_cog and user.id in combat_cog.active_combats:
            await send_response(
                target,
                embed=error_embed(
                    "Combat Active",
                    "You are already in a battle! Finish your fight first using the combat buttons or `!attack`.",
                ),
            )
            return

        summary = None
        enemy = None
        outcome = None

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

            if not player.is_alive():
                await send_response(
                    target,
                    embed=error_embed(
                        "Defeated",
                        "You have 0 HP! Use `!rest` to recover full health before exploring.",
                    ),
                    view=DeadPlayerView(self.bot, user.id),
                )
                return

            outcome = roll_exploration_event(player)
            discovered_quest = None
            is_merchant_discovery = False

            if outcome.event_type == ExplorationEventType.ENCOUNTER_ENEMY:
                enemy = get_random_enemy_for_level(player.level)
            elif outcome.event_type in (
                ExplorationEventType.FIND_GOLD,
                ExplorationEventType.RARE_EVENT,
            ):
                summary = apply_rewards(player, xp=10, gold=outcome.gold_amount)
                uow.players.update(player)
            elif outcome.event_type == ExplorationEventType.FIND_ITEM:
                item_id = outcome.item_id or "health_potion"
                uow.inventories.add_item(user.id, item_id, outcome.item_quantity)
                summary = apply_rewards(
                    player, xp=15, gold=0, drops=[(item_id, outcome.item_quantity)]
                )
                uow.players.update(player)
            elif outcome.event_type == ExplorationEventType.QUEST_EVENT:
                from data.quests import get_available_quests

                all_level_quests = get_available_quests(player.level)
                undiscovered_catalog = []
                merchant_candidates = []

                for q in all_level_quests:
                    status_data = uow.quests.get_quest_status(user.id, q.id)
                    if status_data is None:
                        if q.id in ("lost_caravan", "merchant_supply"):
                            merchant_candidates.append(q)
                        else:
                            undiscovered_catalog.append(q)

                if undiscovered_catalog:
                    discovered_quest = undiscovered_catalog[0]
                    uow.quests.discover_quest(user.id, discovered_quest.id)
                elif merchant_candidates:
                    discovered_quest = merchant_candidates[0]
                    uow.quests.discover_quest(user.id, discovered_quest.id)
                    is_merchant_discovery = True

                summary = apply_rewards(player, xp=20, gold=10)
                uow.players.update(player)
            else:
                summary = apply_rewards(player, xp=20, gold=10)
                uow.players.update(player)

        if (
            outcome
            and outcome.event_type == ExplorationEventType.ENCOUNTER_ENEMY
            and enemy
        ):
            if combat_cog:
                await combat_cog.start_encounter(target, user, enemy)
            return

        if outcome and summary:
            if outcome.event_type in (
                ExplorationEventType.FIND_GOLD,
                ExplorationEventType.RARE_EVENT,
            ):
                embed = success_embed(
                    "Exploration Discovery",
                    f"{outcome.description}\n\n" + "\n".join(summary.messages),
                )
                await send_response(
                    target, embed=embed, view=MainMenuView(self.bot, user.id)
                )
            elif outcome.event_type == ExplorationEventType.FIND_ITEM:
                embed = success_embed(
                    "Loot Found!",
                    f"{outcome.description}\n\n" + "\n".join(summary.messages),
                )
                await send_response(
                    target, embed=embed, view=MainMenuView(self.bot, user.id)
                )
            elif outcome.event_type == ExplorationEventType.QUEST_EVENT:
                from ui.views import MerchantQuestView

                if discovered_quest:
                    if is_merchant_discovery:
                        embed = success_embed(
                            "Merchant Encounter",
                            f"You met a merchant on the road.\n\n"
                            f"The merchant offers you a new quest:\n\n"
                            f"📜 **New Quest Added: {discovered_quest.name}**\n"
                            f"**Objective:** {discovered_quest.objective.description}\n"
                            f"**Reward:** ⭐ {discovered_quest.reward.xp} XP • 🪙 {discovered_quest.reward.gold} Gold\n\n"
                            + "\n".join(summary.messages),
                        )
                    else:
                        embed = success_embed(
                            "Quest Discovery",
                            f"You met a traveler with news of a new assignment!\n\n"
                            f"📜 **New Quest Discovered: {discovered_quest.name}**\n"
                            f"**Objective:** {discovered_quest.objective.description}\n"
                            f"**Reward:** ⭐ {discovered_quest.reward.xp} XP • 🪙 {discovered_quest.reward.gold} Gold\n\n"
                            + "\n".join(summary.messages),
                        )
                    await send_response(
                        target, embed=embed, view=MerchantQuestView(self.bot, user.id)
                    )
                else:
                    embed = success_embed(
                        "Merchant Encounter",
                        "You met a merchant on the road, but you have already discovered all current quests for your level!\n\n"
                        + "\n".join(summary.messages),
                    )
                    await send_response(
                        target, embed=embed, view=MainMenuView(self.bot, user.id)
                    )
            else:
                embed = success_embed(
                    "Exploration Event",
                    f"{outcome.description}\n\n" + "\n".join(summary.messages),
                )
                await send_response(
                    target, embed=embed, view=MainMenuView(self.bot, user.id)
                )

    @commands.command(name="explore", aliases=["adventure"])
    @is_alive()
    async def explore(self, ctx: commands.Context) -> None:
        await self.do_explore(ctx.channel, ctx.author)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdventureCog(bot))
