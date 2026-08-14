from __future__ import annotations

import discord
from discord.ext import commands

from data.items import get_all_items, get_item
from database.unit_of_work import UnitOfWork
from game.economy import buy_item, sell_item
from models.item import ItemType
from ui.views import MainMenuView, PostBuyEquipView
from utils.checks import has_character
from utils.embeds import error_embed, send_response, success_embed
from utils.formatters import format_gold


class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def do_shop(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        user: discord.User | discord.Member,
    ) -> None:
        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(user.id)

        all_items = get_all_items()
        lines = []
        for item in all_items:
            lines.append(
                f"• **{item.name}** (`{item.id}`): **{format_gold(item.buy_price)}**\n"
                f"  *{item.description}* (Sell: {format_gold(item.sell_price)})"
            )

        embed = discord.Embed(
            title="🛒 General Merchant Shop",
            description="\n\n".join(lines)
            + "\n\nUse `!buy <item_id> [quantity]` or `!sell <item_id> [quantity]`.",
            color=discord.Color.gold(),
        )
        if player is not None:
            await send_response(
                target, embed=embed, view=MainMenuView(self.bot, user.id)
            )
        else:
            await send_response(target, embed=embed)

    @commands.command(name="shop")
    async def shop(self, ctx: commands.Context) -> None:
        await self.do_shop(ctx.channel, ctx.author)

    @commands.command(name="buy")
    @has_character()
    async def buy(self, ctx: commands.Context, item_id: str, quantity: int = 1) -> None:
        item_id = item_id.strip().lower()

        if quantity < 1:
            await ctx.send(
                embed=error_embed(
                    "Invalid Quantity",
                    "Quantity must be at least 1.",
                )
            )
            return

        try:
            item_obj = get_item(item_id)
        except KeyError:
            await ctx.send(
                embed=error_embed(
                    "Item Not Found",
                    f"Unknown shop item `{item_id}`.",
                )
            )
            return

        with UnitOfWork() as uow:
            player = uow.players.get_by_discord_id(ctx.author.id)
            if player is None:
                return

            res = buy_item(player, item_obj, quantity)
            if not res.success:
                await ctx.send(
                    embed=error_embed(
                        "Purchase Failed",
                        res.message,
                    )
                )
                return

            uow.players.update(player)
            uow.inventories.add_item(player.discord_id, item_id, quantity)

        is_equipable = item_obj.type in (
            ItemType.WEAPON,
            ItemType.ARMOR,
            ItemType.ACCESSORY,
        ) or (
            isinstance(item_obj.effect_data, dict)
            and any(k in item_obj.effect_data for k in ("attack", "defense", "hp"))
        )

        if is_equipable:
            view = PostBuyEquipView(self.bot, ctx.author.id, item_id, item_obj.name)
            msg = (
                f"{res.message}\n\n"
                f"**To equip it:**\n"
                f"1. Open `!inventory` or click **[Inventory 🎒]**\n"
                f"2. Type `!equip {item_id}` or click **[Equip Now 🛡️]** below.\n\n"
                f"*Equipped items apply their stat bonuses automatically.*"
            )
        else:
            view = MainMenuView(self.bot, ctx.author.id)
            msg = res.message

        await ctx.send(
            embed=success_embed(
                "Purchase Successful",
                msg,
            ),
            view=view,
        )

    @commands.command(name="sell")
    @has_character()
    async def sell(
        self, ctx: commands.Context, item_id: str, quantity: int = 1
    ) -> None:
        item_id = item_id.strip().lower()

        if quantity < 1:
            await ctx.send(
                embed=error_embed(
                    "Invalid Quantity",
                    "Quantity must be at least 1.",
                )
            )
            return

        try:
            item_obj = get_item(item_id)
        except KeyError:
            await ctx.send(
                embed=error_embed(
                    "Item Not Found",
                    f"Unknown item `{item_id}`.",
                )
            )
            return

        with UnitOfWork() as uow:
            owned_qty = uow.inventories.get_item_quantity(ctx.author.id, item_id)
            if owned_qty < quantity:
                await ctx.send(
                    embed=error_embed(
                        "Insufficient Quantity",
                        f"You do not own **{quantity}x {item_obj.name}** in your inventory.",
                    )
                )
                return

            equipped_dict = uow.equipment.get_equipped_items(ctx.author.id)
            equipped_count = sum(
                1 for eq_id in equipped_dict.values() if eq_id == item_id
            )

            if owned_qty - equipped_count < quantity:
                await ctx.send(
                    embed=error_embed(
                        "Cannot Sell Equipped Item",
                        f"**{item_obj.name}** is currently equipped in your equipment slots. "
                        f"Please unequip it first before selling (`!unequip <slot_name>`).",
                    )
                )
                return

            player = uow.players.get_by_discord_id(ctx.author.id)
            if player is None:
                return

            res = sell_item(player, item_obj, quantity)
            uow.inventories.remove_item(ctx.author.id, item_id, quantity)
            uow.players.update(player)

        await ctx.send(
            embed=success_embed(
                "Sale Successful",
                res.message,
            ),
            view=MainMenuView(self.bot, ctx.author.id),
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ShopCog(bot))
