from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands

from config.settings import COMMAND_PREFIX, DISCORD_TOKEN
from database.repositories.player_repository import PlayerRepository
from database.schema_initializer import initialize_schema
from utils.checks import CustomCheckFailure
from utils.embeds import error_embed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=intents,
    help_command=None,
)


async def send_message_safely(
    target: discord.abc.Messageable | None,
    embed: discord.Embed,
    view: discord.ui.View | None = None,
) -> bool:
    if target is None or not isinstance(target, discord.abc.Messageable):
        logger.warning("Target channel is None or not Messageable.")
        return False
    try:
        if view is not None:
            await target.send(embed=embed, view=view)
        else:
            await target.send(embed=embed)
        return True
    except (discord.HTTPException, discord.Forbidden) as exc:
        logger.error("Failed to send message to channel: %s", exc)
        return False


async def load_cogs() -> None:
    cogs_dir = Path(__file__).parent / "cogs"
    for file in cogs_dir.glob("*.py"):
        if file.name != "__init__.py" and file.stat().st_size > 0:
            cog_name = f"cogs.{file.stem}"
            try:
                await bot.load_extension(cog_name)
                logger.info("Loaded cog: %s", cog_name)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to load extension %s: %s", cog_name, exc)


@bot.event
async def setup_hook() -> None:
    initialize_schema()
    await load_cogs()


@bot.event
async def on_ready() -> None:
    if bot.user is not None:
        logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    error = getattr(error, "original", error)
    repo = PlayerRepository()
    player = repo.get_by_discord_id(ctx.author.id) if ctx.author else None

    from ui.views import DeadPlayerView, MainMenuView

    view = None
    if player is not None:
        if player.is_alive():
            view = MainMenuView(bot, ctx.author.id)
        else:
            view = DeadPlayerView(bot, ctx.author.id)

    if isinstance(error, commands.CommandNotFound):
        embed = error_embed(
            "Unknown Command",
            f"The command `{ctx.invoked_with}` was not recognized.",
        )
        await send_message_safely(ctx.channel, embed, view=view)
    elif isinstance(error, CustomCheckFailure):
        embed = error_embed("Action Unavailable", str(error))
        await send_message_safely(ctx.channel, embed, view=view)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = error_embed(
            "Missing Argument",
            f"Missing required parameter: `{error.param.name}`.",
        )
        await send_message_safely(ctx.channel, embed, view=view)
    elif isinstance(error, commands.BadArgument):
        embed = error_embed(
            "Invalid Input",
            "Invalid command argument provided.",
        )
        await send_message_safely(ctx.channel, embed, view=view)
    else:
        logger.error("Unhandled command error: %s", error, exc_info=error)
        embed = error_embed(
            "Error",
            "An unexpected error occurred while executing the command.",
        )
        await send_message_safely(ctx.channel, embed, view=view)


async def main() -> None:
    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
