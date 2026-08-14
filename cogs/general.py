from __future__ import annotations

import discord
from discord.ext import commands

from database.unit_of_work import UnitOfWork
from ui.views import CommandReferenceView, MainMenuView
from utils.embeds import send_response, success_embed


class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def do_commands(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        user: discord.User | discord.Member,
    ) -> None:
        embed = discord.Embed(
            title="📖 DiscordTextRPG Command Reference",
            description="Complete reference for all active game commands and syntax.",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="👤 Character",
            value=(
                "`!start <name>` — Create a new RPG character.\n"
                "`!stats` (alias `!profile`) — View your character stats & equipped gear.\n"
                "`!rest` — Rest at an inn to recover full HP.\n"
                "`!deletecharacter` — Delete your existing character.\n"
                "`!restart <name>` — Reset and recreate your character."
            ),
            inline=False,
        )
        embed.add_field(
            name="🗺️ Adventure",
            value="`!explore` (alias `!adventure`) — Explore the realm to trigger encounters & discover quests.",
            inline=False,
        )
        embed.add_field(
            name="⚔️ Combat",
            value=(
                "`!fight` (alias `!attack`) — Attack the current enemy during battle.\n"
                "`!flee` — Attempt to flee from combat."
            ),
            inline=False,
        )
        embed.add_field(
            name="🎒 Inventory & Equipment",
            value=(
                "`!inventory` (alias `!inv`) — View inventory items and equipped gear.\n"
                "`!equip <item_id>` — Equip a weapon, armor, or accessory.\n"
                "`!unequip <slot_name>` — Unequip gear (`weapon`, `armor`, `accessory_1`, `accessory_2`).\n"
                "`!use <item_id>` — Consume an item (e.g. `!use health_potion`)."
            ),
            inline=False,
        )
        embed.add_field(
            name="🏪 Merchant Shop",
            value=(
                "`!store` (alias `!shop`) — View available items and equipment for sale.\n"
                "`!buy <item_id> [quantity]` — Purchase an item from the merchant.\n"
                "`!sell <item_id> [quantity]` — Sell an item from your inventory."
            ),
            inline=False,
        )
        embed.add_field(
            name="📜 Quests",
            value=(
                "`!quests` — View active, available, completed, and failed quests.\n"
                "`!accept <quest_number>` — Accept a quest using its displayed quest number."
            ),
            inline=False,
        )
        await send_response(
            target, embed=embed, view=CommandReferenceView(self.bot, user.id)
        )

    @commands.command(name="commands", aliases=["help", "check", "allcommands"])
    async def commands_cmd(self, ctx: commands.Context) -> None:
        await self.do_commands(ctx.channel, ctx.author)

    @commands.command(name="hello")
    async def hello(self, ctx: commands.Context) -> None:
        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(ctx.author.id)
        embed = success_embed(
            "Greetings!",
            "Greetings, adventurer! Choose an available action below.",
        )
        if player is not None:
            await ctx.send(embed=embed, view=MainMenuView(self.bot, ctx.author.id))
        else:
            await ctx.send(embed=embed)

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        latency_ms = round(self.bot.latency * 1000)
        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(ctx.author.id)
        embed = success_embed(
            "Pong!",
            f"🏓 Bot API Latency: **{latency_ms}ms**",
        )
        if player is not None:
            await ctx.send(embed=embed, view=MainMenuView(self.bot, ctx.author.id))
        else:
            await ctx.send(embed=embed)

    @commands.command(name="info")
    async def info(self, ctx: commands.Context) -> None:
        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(ctx.author.id)
        embed = discord.Embed(
            title="⚔️ DiscordTextRPG Bot",
            description="A persistent text-based RPG built with Python, discord.py, and SQLite.",
            color=discord.Color.gold(),
        )
        embed.add_field(name="Framework", value="discord.py", inline=True)
        embed.add_field(name="Storage", value="SQLite (WAL Mode)", inline=True)
        embed.add_field(name="Status", value="Active Development 🚧", inline=True)
        if player is not None:
            await ctx.send(embed=embed, view=MainMenuView(self.bot, ctx.author.id))
        else:
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GeneralCog(bot))
