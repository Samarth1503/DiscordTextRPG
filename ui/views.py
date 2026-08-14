from __future__ import annotations

import discord
from discord.ext import commands


class MainMenuView(discord.ui.View):
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

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    @discord.ui.button(label="Explore 🗺️", style=discord.ButtonStyle.primary)
    async def explore_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("AdventureCog")
        if cog:
            await cog.do_explore(interaction, interaction.user)

    @discord.ui.button(label="Profile 📊", style=discord.ButtonStyle.secondary)
    async def profile_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("PlayerCog")
        if cog:
            await cog.do_profile(interaction, interaction.user)

    @discord.ui.button(label="Inventory 🎒", style=discord.ButtonStyle.secondary)
    async def inventory_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("InventoryCog")
        if cog:
            await cog.do_inventory(interaction, interaction.user)

    @discord.ui.button(label="Quests 📜", style=discord.ButtonStyle.secondary)
    async def quests_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("QuestsCog")
        if cog:
            await cog.do_quests(interaction, interaction.user)

    @discord.ui.button(label="Shop 🏪", style=discord.ButtonStyle.secondary)
    async def shop_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("ShopCog")
        if cog:
            await cog.do_shop(interaction, interaction.user)

    @discord.ui.button(label="Rest 🛌", style=discord.ButtonStyle.secondary)
    async def rest_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("PlayerCog")
        if cog:
            await cog.do_rest(interaction, interaction.user)

    @discord.ui.button(
        label="Check All Commands 📖", style=discord.ButtonStyle.secondary, row=1
    )
    async def commands_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("GeneralCog")
        if cog:
            await cog.do_commands(interaction, interaction.user)


class CommandReferenceView(discord.ui.View):
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

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    @discord.ui.button(label="Back 🔙", style=discord.ButtonStyle.primary)
    async def back_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        combat_cog = self.bot.get_cog("CombatCog")
        if combat_cog and interaction.user.id in combat_cog.active_combats:
            ctx_info = combat_cog.active_combats[interaction.user.id]
            from cogs.combat import CombatView
            from database.unit_of_work import UnitOfWork
            from utils.embeds import combat_embed, send_response

            with UnitOfWork() as uow:
                player = uow.players.get_by_discord_id(interaction.user.id)
            if player:
                embed = combat_embed(
                    player, ctx_info.enemy, ["Resumed active combat encounter."]
                )
                view = CombatView(combat_cog, interaction.user.id, ctx_info.enemy)
                await send_response(interaction, embed, view=view)
                return

        player_cog = self.bot.get_cog("PlayerCog")
        if player_cog:
            await player_cog.do_profile(interaction, interaction.user)


class MerchantQuestView(discord.ui.View):
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

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    @discord.ui.button(label="View Quests 📜", style=discord.ButtonStyle.primary)
    async def view_quests_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("QuestsCog")
        if cog:
            await cog.do_quests(interaction, interaction.user)

    @discord.ui.button(
        label="Continue Exploring 🗺️", style=discord.ButtonStyle.secondary
    )
    async def continue_exploring_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("AdventureCog")
        if cog:
            await cog.do_explore(interaction, interaction.user)


class DeadPlayerView(discord.ui.View):
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

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    @discord.ui.button(label="Rest at Inn 🛌", style=discord.ButtonStyle.primary)
    async def rest_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("PlayerCog")
        if cog:
            await cog.do_rest(interaction, interaction.user)

    @discord.ui.button(label="View Profile 📊", style=discord.ButtonStyle.secondary)
    async def profile_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        cog = self.bot.get_cog("PlayerCog")
        if cog:
            await cog.do_profile(interaction, interaction.user)


class PostBuyEquipView(discord.ui.View):
    def __init__(
        self, bot: commands.Bot, player_id: int, item_id: str, item_name: str
    ) -> None:
        super().__init__(timeout=60)
        self.bot = bot
        self.player_id = player_id
        self.item_id = item_id
        self.item_name = item_name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message(
                "This is not your purchase!", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    @discord.ui.button(label="Equip Now 🛡️", style=discord.ButtonStyle.success)
    async def equip_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        self.stop()
        cog = self.bot.get_cog("InventoryCog")
        if cog:
            await cog.do_equip(interaction, interaction.user, self.item_id)

    @discord.ui.button(
        label="Continue Shopping 🏪", style=discord.ButtonStyle.secondary
    )
    async def continue_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        self.stop()
        cog = self.bot.get_cog("ShopCog")
        if cog:
            await cog.do_shop(interaction, interaction.user)
