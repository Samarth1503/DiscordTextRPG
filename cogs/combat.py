from __future__ import annotations

import discord
from discord.ext import commands

from data.enemies import get_random_enemy_for_level
from data.items import get_item
from data.quests import get_quest
from database.unit_of_work import UnitOfWork
from game.combat import CombatContext, execute_turn
from game.rewards import apply_rewards
from models.enemy import Enemy
from models.equipment import Equipment, EquipmentSlot
from utils.action_menu import GameState
from utils.checks import is_alive
from utils.embeds import combat_embed, error_embed, send_response, success_embed


class PostCombatView(discord.ui.View):
    def __init__(self, bot: commands.Bot, player_id: int) -> None:
        super().__init__(timeout=120)
        self.bot = bot
        self.player_id = player_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message(
                "This is not your action menu!", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Explore Again 🗺️", style=discord.ButtonStyle.primary)
    async def explore_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        adv_cog = self.bot.get_cog("AdventureCog")
        if adv_cog:
            await adv_cog.do_explore(interaction, interaction.user)

    @discord.ui.button(label="Rest at Inn 🛌", style=discord.ButtonStyle.secondary)
    async def rest_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        player_cog = self.bot.get_cog("PlayerCog")
        if player_cog:
            await player_cog.do_rest(interaction, interaction.user)

    @discord.ui.button(label="View Inventory 🎒", style=discord.ButtonStyle.secondary)
    async def inventory_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        inv_cog = self.bot.get_cog("InventoryCog")
        if inv_cog:
            await inv_cog.do_inventory(interaction, interaction.user)

    @discord.ui.button(
        label="Check All Commands 📖", style=discord.ButtonStyle.secondary
    )
    async def commands_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        gen_cog = self.bot.get_cog("GeneralCog")
        if gen_cog:
            await gen_cog.do_commands(interaction, interaction.user)

    @discord.ui.button(label="View Quests 📜", style=discord.ButtonStyle.secondary)
    async def quests_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        quests_cog = self.bot.get_cog("QuestsCog")
        if quests_cog:
            await quests_cog.do_quests(interaction, interaction.user)


class CombatView(discord.ui.View):
    def __init__(self, cog: CombatCog, player_id: int, enemy: Enemy) -> None:
        super().__init__(timeout=120)
        self.cog = cog
        self.player_id = player_id
        self.enemy = enemy

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message(
                "This is not your combat encounter!", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Fight ⚔️", style=discord.ButtonStyle.danger)
    async def attack_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        await self.cog.process_turn(
            interaction, self.player_id, action="attack", view=self
        )

    @discord.ui.button(label="Use Potion 🧪", style=discord.ButtonStyle.success)
    async def potion_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        await self.cog.process_potion(interaction, self.player_id, view=self)

    @discord.ui.button(label="Flee 🏃", style=discord.ButtonStyle.secondary)
    async def flee_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        await self.cog.process_turn(
            interaction, self.player_id, action="flee", view=self
        )

    @discord.ui.button(
        label="Check All Commands 📖", style=discord.ButtonStyle.secondary
    )
    async def commands_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        gen_cog = self.cog.bot.get_cog("GeneralCog")
        if gen_cog:
            await gen_cog.do_commands(interaction, interaction.user)


class CombatCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.active_combats: dict[int, CombatContext] = {}

    async def start_encounter(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        user: discord.User | discord.Member,
        enemy: Enemy,
        source: str = "exploration",
        quest_id: str | None = None,
    ) -> None:
        ctx_info = CombatContext(enemy=enemy, source=source, quest_id=quest_id)
        self.active_combats[user.id] = ctx_info

        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(user.id)

        if player is None:
            return

        title_prefix = "⚔️ Quest Combat:" if source == "quest" else "⚔️ Enemy Ambush!"
        embed = combat_embed(
            player, enemy, [f"{title_prefix} Battle started against **{enemy.name}**!"]
        )
        view = CombatView(self, user.id, enemy)
        await send_response(target, embed, view=view)

    @commands.command(name="fight", aliases=["battle"])
    @is_alive()
    async def fight(self, ctx: commands.Context) -> None:
        if ctx.author.id in self.active_combats:
            await ctx.send(
                embed=error_embed(
                    "Combat Active",
                    "You are already in an active battle! Use the buttons below or type `!attack`.",
                    state=GameState.COMBAT,
                )
            )
            return

        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(ctx.author.id)

        if player is None:
            return

        enemy = get_random_enemy_for_level(player.level)
        await self.start_encounter(ctx.channel, ctx.author, enemy, source="exploration")

    @commands.command(name="attack")
    @is_alive()
    async def attack(self, ctx: commands.Context) -> None:
        if ctx.author.id not in self.active_combats:
            await ctx.send(
                embed=error_embed(
                    "No Active Battle",
                    "You are not in combat. Use `!explore` or `!fight`.",
                    state=GameState.NORMAL,
                )
            )
            return

        await self.process_turn(ctx.channel, ctx.author.id, action="attack")

    @commands.command(name="flee")
    @is_alive()
    async def flee(self, ctx: commands.Context) -> None:
        if ctx.author.id not in self.active_combats:
            await ctx.send(
                embed=error_embed(
                    "No Active Battle", "You are not in combat.", state=GameState.NORMAL
                )
            )
            return

        await self.process_turn(ctx.channel, ctx.author.id, action="flee")

    async def process_potion(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        player_id: int,
        view: CombatView | None = None,
    ) -> None:
        if player_id not in self.active_combats:
            await send_response(
                target,
                embed=error_embed("No Active Battle", "You are not in combat."),
            )
            return

        ctx_info = self.active_combats[player_id]

        with UnitOfWork() as uow:
            if not uow.inventories.has_item(player_id, "health_potion", 1):
                embed = error_embed(
                    "No Potions!",
                    "You don't have any Health Potions in your inventory! Buy some at `!shop`.",
                )
                await send_response(target, embed)
                return

            player = uow.players.get_by_discord_id(player_id)
            if player is None:
                return

            uow.inventories.remove_item(player_id, "health_potion", 1)
            healed = player.heal(50)
            uow.players.update(player)

            log_msg = [
                f"🧪 **{player.name}** used a Health Potion restoring **+{healed} HP**!"
            ]
            embed = combat_embed(player, ctx_info.enemy, log_msg)
            await send_response(target, embed, view=view)

    async def process_turn(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        player_id: int,
        action: str,
        view: CombatView | None = None,
    ) -> None:
        if player_id not in self.active_combats:
            await send_response(
                target,
                embed=error_embed(
                    "No Active Battle",
                    "Combat has already ended or is not active.",
                ),
            )
            return

        ctx_info = self.active_combats[player_id]
        enemy = ctx_info.enemy

        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(player_id)
            if player is None:
                return

            equipped_dict = uow.equipment.get_equipped_items(player_id)
            eq = Equipment()
            for slot, item_id in equipped_dict.items():
                if item_id:
                    try:
                        item_obj = get_item(item_id)
                        if slot == EquipmentSlot.WEAPON:
                            eq.weapon = item_obj
                        elif slot == EquipmentSlot.ARMOR:
                            eq.armor = item_obj
                        elif slot == EquipmentSlot.ACCESSORY_1:
                            eq.accessory_1 = item_obj
                        elif slot == EquipmentSlot.ACCESSORY_2:
                            eq.accessory_2 = item_obj
                    except KeyError:
                        pass

            bonuses = eq.calculate_total_bonus()
            _, eff_atk, eff_def = player.calculate_total_stats(bonuses)

            turn_res = execute_turn(
                player,
                enemy,
                action=action,
                effective_attack=eff_atk,
                effective_defense=eff_def,
            )

            if not enemy.is_alive():
                self.active_combats.pop(player_id, None)
                drops = enemy.roll_loot()
                for item_id, qty in drops:
                    uow.inventories.add_item(player_id, item_id, qty)

                summary = apply_rewards(
                    player,
                    xp=enemy.xp_reward,
                    gold=enemy.gold_reward,
                    drops=drops,
                )
                uow.players.update(player)

                quest_complete_msg = ""
                if ctx_info.source == "quest" and ctx_info.quest_id:
                    q_obj = get_quest(ctx_info.quest_id)
                    status_data = uow.quests.get_quest_status(
                        player_id, ctx_info.quest_id
                    )
                    if status_data and status_data[1] == "ACTIVE":
                        current_prog = status_data[0]
                        new_prog = current_prog + 1
                        uow.quests.update_progress(
                            player_id, ctx_info.quest_id, new_prog
                        )
                        if q_obj.is_complete(new_prog):
                            uow.quests.complete_quest(player_id, ctx_info.quest_id)
                            for item_id, qty in q_obj.reward.items:
                                uow.inventories.add_item(player_id, item_id, qty)
                            q_summary = apply_rewards(
                                player,
                                xp=q_obj.reward.xp,
                                gold=q_obj.reward.gold,
                                drops=q_obj.reward.items,
                            )
                            uow.players.update(player)
                            quest_complete_msg = (
                                f"\n\n🏆 **QUEST COMPLETED: {q_obj.name}!**\n"
                                + "\n".join(q_summary.messages)
                            )
                        else:
                            quest_complete_msg = f"\n\n📜 **Quest Progress Updated:** {q_obj.name} ({new_prog}/{q_obj.objective.target_amount})"

                embed = success_embed(
                    f"🎉 VICTORY! Defeated {enemy.name}",
                    "\n".join(turn_res.log_messages)
                    + "\n\n**Rewards Earned:**\n"
                    + "\n".join(summary.messages)
                    + quest_complete_msg,
                )
                if view:
                    view.stop()

                post_view = PostCombatView(self.bot, player_id)
                await send_response(target, embed, view=post_view)

            elif not player.is_alive():
                self.active_combats.pop(player_id, None)
                uow.players.update(player)

                embed = error_embed(
                    f"💀 DEFEAT! You were slain by {enemy.name}",
                    "\n".join(turn_res.log_messages)
                    + "\n\nYou have **0 HP**. Rest at the tavern (`!rest`) for free to recover your health!",
                )
                if view:
                    view.stop()

                from ui.views import DeadPlayerView

                post_view = DeadPlayerView(self.bot, player_id)
                await send_response(target, embed, view=post_view)

            elif action == "flee" and any(
                "successfully fled" in log for log in turn_res.log_messages
            ):
                self.active_combats.pop(player_id, None)
                uow.players.update(player)

                if ctx_info.source == "quest" and ctx_info.quest_id:
                    uow.quests.fail_quest(player_id, ctx_info.quest_id)
                    q_obj = get_quest(ctx_info.quest_id)
                    embed = error_embed(
                        f"🏃 Fled from {enemy.name} — Quest Failed!",
                        f"❌ **Quest Failed: {q_obj.name}**\n\nYou abandoned the quest by fleeing from combat.",
                    )
                else:
                    embed = success_embed(
                        "Escaped Combat",
                        "\n".join(turn_res.log_messages),
                    )

                if view:
                    view.stop()

                post_view = PostCombatView(self.bot, player_id)
                await send_response(target, embed, view=post_view)

            else:
                uow.players.update(player)
                embed = combat_embed(player, enemy, turn_res.log_messages)
                await send_response(target, embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CombatCog(bot))
