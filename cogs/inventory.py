from __future__ import annotations

import discord
from discord.ext import commands

from data.items import get_item
from database.unit_of_work import UnitOfWork
from models.equipment import EquipmentSlot
from models.item import ItemType
from ui.views import MainMenuView
from utils.checks import has_character
from utils.embeds import error_embed, send_response, success_embed


class InventoryCog(commands.Cog):
    SLOT_NAMES: dict[str, EquipmentSlot] = {
        "weapon": EquipmentSlot.WEAPON,
        "armor": EquipmentSlot.ARMOR,
        "accessory_1": EquipmentSlot.ACCESSORY_1,
        "accessory_2": EquipmentSlot.ACCESSORY_2,
    }

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def do_inventory(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        user: discord.User | discord.Member,
    ) -> None:
        with UnitOfWork() as uow:
            items = uow.inventories.get_inventory(user.id)
            equipped_dict = uow.equipment.get_equipped_items(user.id)

        embed = discord.Embed(
            title=f"🎒 {user.display_name}'s Inventory",
            color=discord.Color.blue(),
        )

        eq_lines = []
        for slot in (
            EquipmentSlot.WEAPON,
            EquipmentSlot.ARMOR,
            EquipmentSlot.ACCESSORY_1,
            EquipmentSlot.ACCESSORY_2,
        ):
            eq_item_id = equipped_dict.get(slot)
            slot_title = slot.value.replace("_", " ").title()
            if eq_item_id:
                try:
                    eq_obj = get_item(eq_item_id)
                    stats_list = []
                    if isinstance(eq_obj.effect_data, dict):
                        atk = eq_obj.effect_data.get("attack", 0)
                        df = eq_obj.effect_data.get("defense", 0)
                        hp = eq_obj.effect_data.get("hp", 0)
                        if atk:
                            stats_list.append(f"+{atk} Atk")
                        if df:
                            stats_list.append(f"+{df} Def")
                        if hp:
                            stats_list.append(f"+{hp} HP")
                    stat_str = f" ({', '.join(stats_list)})" if stats_list else ""
                    eq_lines.append(f"• **{slot_title}**: **{eq_obj.name}**{stat_str}")
                except KeyError:
                    eq_lines.append(f"• **{slot_title}**: `{eq_item_id}`")
            else:
                eq_lines.append(f"• **{slot_title}**: *Empty*")

        embed.add_field(
            name="🛡️ Currently Equipped",
            value="\n".join(eq_lines),
            inline=False,
        )

        if items:
            inv_lines = []
            for item_id, qty in items:
                try:
                    item_obj = get_item(item_id)
                    inv_lines.append(
                        f"• **{item_obj.name}** (`{item_id}`): x{qty} — *{item_obj.description}*"
                    )
                except KeyError:
                    inv_lines.append(f"• `{item_id}`: x{qty}")
            embed.add_field(
                name="🎒 Backpack Items",
                value="\n".join(inv_lines),
                inline=False,
            )
        else:
            embed.add_field(
                name="🎒 Backpack Items",
                value="*Your backpack is empty.*",
                inline=False,
            )

        embed.set_footer(
            text="Use !equip <item_id> [slot] to equip | !unequip <slot_name> to unequip | !use <item_id> to consume"
        )
        await send_response(target, embed=embed, view=MainMenuView(self.bot, user.id))

    @commands.command(name="inventory", aliases=["inv"])
    @has_character()
    async def inventory(self, ctx: commands.Context) -> None:
        await self.do_inventory(ctx.channel, ctx.author)

    @commands.command(name="use")
    @has_character()
    async def use(self, ctx: commands.Context, item_id: str) -> None:
        item_id = item_id.strip().lower()

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

        if item_obj.type != ItemType.CONSUMABLE:
            await ctx.send(
                embed=error_embed(
                    "Cannot Use",
                    f"**{item_obj.name}** is not a consumable item!",
                )
            )
            return

        with UnitOfWork() as uow:
            if not uow.inventories.has_item(ctx.author.id, item_id, 1):
                await ctx.send(
                    embed=error_embed(
                        "Not In Inventory",
                        f"You do not own any **{item_obj.name}**.",
                    )
                )
                return

            player = uow.players.get_by_discord_id(ctx.author.id)
            if player is None:
                return

            heal_val = item_obj.effect_data.get("heal_hp", 0)
            if heal_val > 0:
                healed = player.heal(heal_val)
                uow.inventories.remove_item(ctx.author.id, item_id, 1)
                uow.players.update(player)
                embed = success_embed(
                    "Item Consumed",
                    f"🧪 Consumed **{item_obj.name}** and restored **+{healed} HP**! (Current HP: {player.hp}/{player.max_hp})",
                )
                await ctx.send(embed=embed, view=MainMenuView(self.bot, ctx.author.id))

    async def do_equip(
        self,
        target: discord.abc.Messageable | discord.Interaction,
        user: discord.User | discord.Member,
        item_id: str,
        slot_name: str | None = None,
    ) -> None:
        item_id = item_id.strip().lower()

        try:
            item_obj = get_item(item_id)
        except KeyError:
            await send_response(
                target,
                embed=error_embed("Item Not Found", f"Unknown item `{item_id}`."),
            )
            return

        is_equipable = item_obj.type in (
            ItemType.WEAPON,
            ItemType.ARMOR,
            ItemType.ACCESSORY,
        ) or (
            isinstance(item_obj.effect_data, dict)
            and any(k in item_obj.effect_data for k in ("attack", "defense", "hp"))
        )

        if not is_equipable:
            await send_response(
                target,
                embed=error_embed(
                    "Cannot Equip", f"**{item_obj.name}** is not an equipable item."
                ),
            )
            return

        with UnitOfWork() as uow:
            if not uow.inventories.has_item(user.id, item_id, 1):
                await send_response(
                    target,
                    embed=error_embed(
                        "Not In Inventory", f"You do not own **{item_obj.name}**."
                    ),
                )
                return

            equipped = uow.equipment.get_equipped_items(user.id)

            if item_obj.type == ItemType.WEAPON:
                slot = EquipmentSlot.WEAPON
            elif item_obj.type == ItemType.ARMOR:
                slot = EquipmentSlot.ARMOR
            else:
                if slot_name and slot_name.strip().lower() in self.SLOT_NAMES:
                    slot = self.SLOT_NAMES[slot_name.strip().lower()]
                    if slot not in (
                        EquipmentSlot.ACCESSORY_1,
                        EquipmentSlot.ACCESSORY_2,
                    ):
                        slot = EquipmentSlot.ACCESSORY_1
                else:
                    if equipped.get(EquipmentSlot.ACCESSORY_1) is None:
                        slot = EquipmentSlot.ACCESSORY_1
                    elif equipped.get(EquipmentSlot.ACCESSORY_2) is None:
                        slot = EquipmentSlot.ACCESSORY_2
                    else:
                        slot = EquipmentSlot.ACCESSORY_1

            prev_item_id = uow.equipment.equip_item(user.id, slot, item_id)
            uow.inventories.remove_item(user.id, item_id, 1)
            if prev_item_id:
                uow.inventories.add_item(user.id, prev_item_id, 1)

            player = uow.players.get_by_discord_id(user.id)
            equipped_dict = uow.equipment.get_equipped_items(user.id)

            from models.equipment import Equipment

            eq = Equipment()
            for s, i_id in equipped_dict.items():
                if i_id:
                    try:
                        i_obj = get_item(i_id)
                        if s == EquipmentSlot.WEAPON:
                            eq.weapon = i_obj
                        elif s == EquipmentSlot.ARMOR:
                            eq.armor = i_obj
                        elif s == EquipmentSlot.ACCESSORY_1:
                            eq.accessory_1 = i_obj
                        elif s == EquipmentSlot.ACCESSORY_2:
                            eq.accessory_2 = i_obj
                    except KeyError:
                        pass

            bonuses = eq.calculate_total_bonus()
            tot_hp, tot_atk, tot_def = (
                player.calculate_total_stats(bonuses) if player else (100, 10, 5)
            )

        slot_title = slot.value.replace("_", " ").title()
        msg = f"🛡️ Equipped **{item_obj.name}** to **{slot_title}** slot!"
        if prev_item_id:
            try:
                prev_obj = get_item(prev_item_id)
                msg += f"\n(Unequipped **{prev_obj.name}** back to inventory)"
            except KeyError:
                msg += f"\n(Unequipped `{prev_item_id}` back to inventory)"

        stats_list = []
        if isinstance(item_obj.effect_data, dict):
            atk = item_obj.effect_data.get("attack", 0)
            df = item_obj.effect_data.get("defense", 0)
            hp = item_obj.effect_data.get("hp", 0)
            if atk:
                stats_list.append(f"+{atk} Attack")
            if df:
                stats_list.append(f"+{df} Defense")
            if hp:
                stats_list.append(f"+{hp} HP")

        if stats_list:
            msg += f"\n\n**Stat Bonus:** {', '.join(stats_list)}"
        msg += f"\n**Effective Stats:** Attack {tot_atk} | Defense {tot_def} | Max HP {tot_hp}"

        embed = success_embed("Item Equipped", msg)
        await send_response(target, embed=embed, view=MainMenuView(self.bot, user.id))

    @commands.command(name="equip")
    @has_character()
    async def equip(
        self, ctx: commands.Context, item_id: str, slot_name: str | None = None
    ) -> None:
        await self.do_equip(ctx.channel, ctx.author, item_id, slot_name)

    @commands.command(name="unequip")
    @has_character()
    async def unequip(self, ctx: commands.Context, slot_name: str) -> None:
        slot_name = slot_name.strip().lower()

        slot = self.SLOT_NAMES.get(slot_name)
        if slot is None:
            valid = ", ".join(f"`{s}`" for s in self.SLOT_NAMES)
            await ctx.send(
                embed=error_embed(
                    "Invalid Slot",
                    f"Unknown equipment slot `{slot_name}`.\nValid slots: {valid}",
                )
            )
            return

        with UnitOfWork() as uow:
            prev_item_id = uow.equipment.unequip_slot(ctx.author.id, slot)
            if prev_item_id is None:
                await ctx.send(
                    embed=error_embed(
                        "Slot Empty",
                        f"Your **{slot.value.replace('_', ' ').title()}** slot is already empty.",
                    )
                )
                return

            uow.inventories.add_item(ctx.author.id, prev_item_id, 1)

            player = uow.players.get_by_discord_id(ctx.author.id)
            equipped_dict = uow.equipment.get_equipped_items(ctx.author.id)

            from models.equipment import Equipment

            eq = Equipment()
            for s, i_id in equipped_dict.items():
                if i_id:
                    try:
                        i_obj = get_item(i_id)
                        if s == EquipmentSlot.WEAPON:
                            eq.weapon = i_obj
                        elif s == EquipmentSlot.ARMOR:
                            eq.armor = i_obj
                        elif s == EquipmentSlot.ACCESSORY_1:
                            eq.accessory_1 = i_obj
                        elif s == EquipmentSlot.ACCESSORY_2:
                            eq.accessory_2 = i_obj
                    except KeyError:
                        pass

            bonuses = eq.calculate_total_bonus()
            tot_hp, tot_atk, tot_def = (
                player.calculate_total_stats(bonuses) if player else (100, 10, 5)
            )

        try:
            item_obj = get_item(prev_item_id)
            item_display = item_obj.name
        except KeyError:
            item_display = prev_item_id

        slot_title = slot.value.replace("_", " ").title()
        msg = (
            f"🔓 Removed **{item_display}** from **{slot_title}** slot and returned it to your inventory.\n\n"
            f"**Effective Stats:** Attack {tot_atk} | Defense {tot_def} | Max HP {tot_hp}"
        )
        embed = success_embed("Item Unequipped", msg)
        await ctx.send(embed=embed, view=MainMenuView(self.bot, ctx.author.id))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InventoryCog(bot))
