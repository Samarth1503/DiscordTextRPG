from __future__ import annotations

from discord.ext import commands

from database.repositories.player_repository import PlayerRepository


class CustomCheckFailure(commands.CheckFailure):
    pass


def has_character():
    async def predicate(ctx: commands.Context) -> bool:
        repo = PlayerRepository()
        player = repo.get_by_discord_id(ctx.author.id)
        if player is None:
            raise CustomCheckFailure(
                "You do not have a character yet! Use `!start <name>` to begin."
            )
        return True

    return commands.check(predicate)


def is_alive():
    async def predicate(ctx: commands.Context) -> bool:
        repo = PlayerRepository()
        player = repo.get_by_discord_id(ctx.author.id)
        if player is None:
            raise CustomCheckFailure(
                "You do not have a character yet! Use `!start <name>` to begin."
            )
        if not player.is_alive():
            raise CustomCheckFailure(
                "You are defeated and cannot take action! Rest at the tavern (`!rest`) to recover."
            )
        return True

    return commands.check(predicate)
