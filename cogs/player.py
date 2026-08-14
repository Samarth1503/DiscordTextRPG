from __future__ import annotations

import discord
from discord.ext import commands

from config.settings import MAX_CHARACTER_NAME_LENGTH
from database.unit_of_work import UnitOfWork
from models.player import Player
from ui.views import MainMenuView
from utils.checks import has_character
from utils.embeds import error_embed, profile_embed, send_response, success_embed


class ConfirmDeleteView(discord.ui.View):
    def __init__(
        self, cog: PlayerCog, player_id: int, new_name: str | None = None
    ) -> None:
        super().__init__(timeout=60)
        self.cog = cog
        self.player_id = player_id
        self.new_name = new_name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message(
                "This confirmation is not for you!", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Confirm Delete / Reset ⚠️", style=discord.ButtonStyle.danger
    )
    async def confirm_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        self.stop()

        with UnitOfWork() as uow:
            uow.players.delete(self.player_id)

        if self.new_name:
            with UnitOfWork() as uow:
                new_player = Player(
                    discord_id=self.player_id,
                    name=self.new_name,
                    gold=20,
                )
                uow.players.create(new_player)
                uow.inventories.add_item(self.player_id, "health_potion", 2)

            embed = success_embed(
                "Character Restarted!",
                f"🔄 Your character has been reset!\nWelcome your new hero: **{self.new_name}** (Level 1, 20 Gold 🪙, 2x Health Potions 🧪).",
            )
            await interaction.channel.send(
                embed=embed, view=MainMenuView(self.cog.bot, self.player_id)
            )
        else:
            embed = success_embed(
                "Character Deleted",
                "🗑️ Your character profile and all associated data have been permanently deleted.",
            )
            await interaction.channel.send(embed=embed)

    @discord.ui.button(label="Cancel ❌", style=discord.ButtonStyle.secondary)
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        self.stop()
        embed = error_embed(
            "Cancelled",
            "Character deletion/restart was cancelled.",
        )
        await interaction.channel.send(embed=embed)


class PlayerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def do_profile(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        user: discord.User | discord.Member,
    ) -> None:
        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(user.id)
            equipped_dict = uow.equipment.get_equipped_items(user.id)

            from data.items import get_item
            from models.equipment import Equipment, EquipmentSlot

            eq = Equipment()
            for slot, item_id in equipped_dict.items():
                if item_id:
                    item_obj = get_item(item_id)
                    if slot == EquipmentSlot.WEAPON:
                        eq.weapon = item_obj
                    elif slot == EquipmentSlot.ARMOR:
                        eq.armor = item_obj
                    elif slot == EquipmentSlot.ACCESSORY_1:
                        eq.accessory_1 = item_obj
                    elif slot == EquipmentSlot.ACCESSORY_2:
                        eq.accessory_2 = item_obj

        if player is None:
            await send_response(
                target, embed=error_embed("Not Found", "Character not found.")
            )
            return

        embed = profile_embed(player, eq)
        await send_response(target, embed=embed, view=MainMenuView(self.bot, user.id))

    async def do_rest(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        user: discord.User | discord.Member,
    ) -> None:
        standard_cost = 10
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

            if player.hp >= player.max_hp:
                await send_response(
                    target,
                    embed=error_embed(
                        "Full Health",
                        "You are already at full HP!",
                    ),
                )
                return

            actual_cost = min(player.gold, standard_cost)
            player.gold -= actual_cost
            healed = player.heal(player.max_hp)
            uow.players.update(player)

        cost_msg = (
            f"spent **{actual_cost} gold**"
            if actual_cost > 0
            else "rested for **FREE** (Tavern Charity for broke adventurers)"
        )
        embed = success_embed(
            "Rested & Recovered",
            f"🛌 You {cost_msg} and recovered to **full HP** (+{healed} HP restored)! (HP: {player.hp}/{player.max_hp})",
        )
        await send_response(target, embed=embed, view=MainMenuView(self.bot, user.id))

    @commands.command(name="start")
    async def start(self, ctx: commands.Context, *, name: str | None = None) -> None:
        if not name or not name.strip():
            await ctx.send(
                embed=error_embed(
                    "Invalid Name",
                    "Please provide a character name!\nUsage: `!start <YourName>`",
                )
            )
            return

        name = name.strip()

        if len(name) > MAX_CHARACTER_NAME_LENGTH:
            await ctx.send(
                embed=error_embed(
                    "Invalid Name",
                    f"Character name cannot exceed {MAX_CHARACTER_NAME_LENGTH} characters.",
                )
            )
            return

        with UnitOfWork() as uow:
            existing = uow.players.get_by_discord_id(ctx.author.id)
            if existing is not None:
                await ctx.send(
                    embed=error_embed(
                        "Character Exists",
                        f"You already have a character named **{existing.name}**!",
                    )
                )
                return

            player = Player(
                discord_id=ctx.author.id,
                name=name,
                gold=20,
            )
            uow.players.create(player)
            uow.inventories.add_item(ctx.author.id, "health_potion", 2)

        embed = success_embed(
            f"Welcome to DiscordTextRPG, {player.name}!",
            f"Your character **{player.name}** has been created at **Level 1**!\nYou have been granted **20 Gold** 🪙 and **2x Health Potions** 🧪 to start your journey.",
        )
        await ctx.send(embed=embed, view=MainMenuView(self.bot, ctx.author.id))

    @commands.command(name="stats", aliases=["profile"])
    @has_character()
    async def stats(self, ctx: commands.Context) -> None:
        await self.do_profile(ctx.channel, ctx.author)

    @commands.command(name="rest")
    @has_character()
    async def rest(self, ctx: commands.Context) -> None:
        await self.do_rest(ctx.channel, ctx.author)

    @commands.command(
        name="deletecharacter", aliases=["deleteprofile", "resetcharacter"]
    )
    @has_character()
    async def deletecharacter(self, ctx: commands.Context) -> None:
        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(ctx.author.id)

        if player is None:
            return

        embed = error_embed(
            "⚠️ Delete Character Warning",
            f"Are you sure you want to delete **{player.name}** (Level {player.level})?\nThis will permanently delete your character, inventory, gear, and quest progress!",
        )
        view = ConfirmDeleteView(self, ctx.author.id)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="restart", aliases=["reset"])
    @has_character()
    async def restart(
        self, ctx: commands.Context, *, new_name: str | None = None
    ) -> None:
        if not new_name or not new_name.strip():
            await ctx.send(
                embed=error_embed(
                    "Missing Name",
                    "Please specify a new character name!\nUsage: `!restart <NewName>`",
                )
            )
            return

        new_name = new_name.strip()
        if len(new_name) > MAX_CHARACTER_NAME_LENGTH:
            await ctx.send(
                embed=error_embed(
                    "Invalid Name",
                    f"Character name cannot exceed {MAX_CHARACTER_NAME_LENGTH} characters.",
                )
            )
            return

        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(ctx.author.id)

        if player is None:
            return

        embed = error_embed(
            "⚠️ Reset Character Warning",
            f"Are you sure you want to reset your character **{player.name}** and start fresh as **{new_name}**?\nYour current level, inventory, gear, and gold will be deleted and reset to Level 1!",
        )
        view = ConfirmDeleteView(self, ctx.author.id, new_name=new_name)
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PlayerCog(bot))
