from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import discord
import pytest

from data.enemies import get_enemy
from data.quests import get_quest
from database.unit_of_work import UnitOfWork
from game.combat import CombatContext, TurnResult
from models.player import Player
from ui.views import CommandReferenceView
from cogs.combat import CombatCog, PostCombatView
from cogs.general import GeneralCog
from cogs.quests import QuestsCog


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ==================================================
# PASS TEST CASES
# ==================================================


@pytest.mark.anyio
async def test_pass_1_check_commands_normal_gameplay():
    bot = MagicMock()
    cog = GeneralCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 1001

    await cog.do_commands(target, user)
    target.response.edit_message.assert_awaited_once()

    _, kwargs = target.response.edit_message.call_args
    embed = kwargs.get("embed")
    assert embed is not None
    assert "Command Reference" in embed.title
    assert isinstance(kwargs.get("view"), CommandReferenceView)


def test_pass_2_victory_prompt_has_check_commands():
    bot = MagicMock()
    view = PostCombatView(bot, player_id=1002)
    labels = [btn.label for btn in view.children if isinstance(btn, discord.ui.Button)]

    assert "Explore Again 🗺️" in labels
    assert "Rest at Inn 🛌" in labels
    assert "View Inventory 🎒" in labels
    assert "Check All Commands 📖" in labels


@pytest.mark.anyio
async def test_pass_3_check_commands_does_not_alter_player_state(db_path):
    player = Player(
        discord_id=1003,
        name="StatCheck",
        level=2,
        hp=45,
        max_hp=50,
        experience=120,
        gold=350,
    )
    with UnitOfWork() as uow:
        uow.players.create(player)

    bot = MagicMock()
    cog = GeneralCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 1003

    await cog.do_commands(target, user)

    with UnitOfWork() as fresh_uow:
        p_after = fresh_uow.players.get_by_discord_id(1003)
        assert p_after.hp == 45
        assert p_after.max_hp == 50
        assert p_after.experience == 120
        assert p_after.gold == 350
        assert p_after.level == 2


def test_pass_4_quest_discovery(db_path):
    player = Player(discord_id=1004, name="Explorer")
    with UnitOfWork() as uow:
        uow.players.create(player)
        discovered = uow.quests.get_discovered_quests(1004)
        assert len(discovered) == 0

        uow.quests.discover_quest(1004, "herb_collector")
        discovered_after = uow.quests.get_discovered_quests(1004)
        assert "herb_collector" in discovered_after


@pytest.mark.anyio
async def test_pass_5_6_quest_acceptance_and_persistence(db_path):
    player = Player(discord_id=1005, name="QQuest")
    with UnitOfWork() as uow:
        uow.players.create(player)
        uow.quests.assign_quest(1005, "herb_collector")

    with UnitOfWork() as fresh_uow:
        active = fresh_uow.quests.get_active_quests(1005)
        assert len(active) == 1
        q_id, prog, status = active[0]
        assert q_id == "herb_collector"
        assert prog == 0
        assert status == "ACTIVE"


@pytest.mark.anyio
async def test_pass_7_quest_combat_starts_automatically(db_path):
    player = Player(discord_id=1007, name="AutoCombat")
    with UnitOfWork() as uow:
        uow.players.create(player)

    bot = MagicMock()
    quests_cog = QuestsCog(bot)
    combat_cog = CombatCog(bot)
    bot.get_cog.side_effect = lambda name: combat_cog if name == "CombatCog" else None

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 1007

    await quests_cog.execute_accept_quest(target, user, "goblin_slayer")

    assert 1007 in combat_cog.active_combats
    ctx_info = combat_cog.active_combats[1007]
    assert ctx_info.source == "quest"
    assert ctx_info.quest_id == "goblin_slayer"


@pytest.mark.anyio
async def test_pass_8_9_quest_flee_fails_quest(db_path, monkeypatch):
    player = Player(discord_id=1009, name="FleeingHero", hp=100, max_hp=100, attack=50)
    with UnitOfWork() as uow:
        uow.players.create(player)
        uow.quests.assign_quest(1009, "goblin_slayer")

    bot = MagicMock()
    combat_cog = CombatCog(bot)

    enemy = get_enemy("goblin")
    combat_cog.active_combats[1009] = CombatContext(
        enemy=enemy, source="quest", quest_id="goblin_slayer"
    )

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    mock_turn_result = TurnResult(
        player_hp=100,
        enemy_hp=35,
        player_damage_dealt=0,
        enemy_damage_dealt=0,
        is_player_crit=False,
        is_enemy_crit=False,
        log_messages=["🏃 FleeingHero successfully fled from battle!"],
    )
    monkeypatch.setattr(
        "cogs.combat.execute_turn", lambda *args, **kwargs: mock_turn_result
    )

    await combat_cog.process_turn(target, 1009, action="flee")

    assert 1009 not in combat_cog.active_combats

    with UnitOfWork() as fresh_uow:
        status_data = fresh_uow.quests.get_quest_status(1009, "goblin_slayer")
        assert status_data is not None
        _, status = status_data
        assert status == "FAILED"


@pytest.mark.anyio
async def test_pass_10_11_12_quest_progress_completion_and_persistence(db_path):
    player = Player(
        discord_id=1010, name="Slayer", level=1, hp=100, max_hp=100, attack=100, gold=0
    )
    with UnitOfWork() as uow:
        uow.players.create(player)
        uow.quests.assign_quest(1010, "goblin_slayer")

    bot = MagicMock()
    combat_cog = CombatCog(bot)

    q_obj = get_quest("goblin_slayer")
    kills_needed = q_obj.objective.target_amount

    for i in range(kills_needed):
        enemy = get_enemy("goblin")
        enemy.hp = 1
        combat_cog.active_combats[1010] = CombatContext(
            enemy=enemy, source="quest", quest_id="goblin_slayer"
        )

        target = AsyncMock(spec=discord.Interaction)
        target.response = MagicMock()
        target.response.is_done.return_value = False
        target.response.edit_message = AsyncMock()

        await combat_cog.process_turn(target, 1010, action="attack")

    with UnitOfWork() as fresh_uow:
        status_data = fresh_uow.quests.get_quest_status(1010, "goblin_slayer")
        assert status_data is not None
        prog, status = status_data
        assert prog == kills_needed
        assert status == "COMPLETED"

        p_after = fresh_uow.players.get_by_discord_id(1010)
        assert p_after.gold > 0


# ==================================================
# FAIL & EDGE TEST CASES
# ==================================================


@pytest.mark.anyio
async def test_fail_2_accept_nonexistent_quest(db_path):
    player = Player(discord_id=2002, name="Tester")
    with UnitOfWork() as uow:
        uow.players.create(player)

    bot = MagicMock()
    cog = QuestsCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 2002

    await cog.execute_accept_quest(target, user, "nonexistent_quest_id")

    with UnitOfWork() as fresh_uow:
        active = fresh_uow.quests.get_active_quests(2002)
        assert len(active) == 0


@pytest.mark.anyio
async def test_fail_4_accept_already_active_quest(db_path):
    player = Player(discord_id=2004, name="DoubleAccept")
    with UnitOfWork() as uow:
        uow.players.create(player)
        uow.quests.assign_quest(2004, "herb_collector")

    bot = MagicMock()
    cog = QuestsCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 2004

    await cog.execute_accept_quest(target, user, "herb_collector")

    with UnitOfWork() as fresh_uow:
        active = fresh_uow.quests.get_active_quests(2004)
        assert len(active) == 1


@pytest.mark.anyio
async def test_fail_7_fight_without_combat():
    bot = MagicMock()
    cog = CombatCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    await cog.process_turn(target, player_id=9999, action="attack")

    target.response.edit_message.assert_awaited_once()
    _, kwargs = target.response.edit_message.call_args
    embed = kwargs.get("embed")
    assert embed is not None
    assert "No Active Battle" in embed.title


@pytest.mark.anyio
async def test_fail_15_nonexistent_player_quest_action():
    bot = MagicMock()
    cog = QuestsCog(bot)

    target = AsyncMock(spec=discord.Interaction)
    target.response = MagicMock()
    target.response.is_done.return_value = False
    target.response.edit_message = AsyncMock()

    user = MagicMock()
    user.id = 888888

    await cog.do_quests(target, user)

    target.response.edit_message.assert_awaited_once()
    _, kwargs = target.response.edit_message.call_args
    embed = kwargs.get("embed")
    assert embed is not None
    assert "No Character" in embed.title
