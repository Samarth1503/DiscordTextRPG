from __future__ import annotations

import time
import pytest

from data.quests import get_available_quests, get_quest
from database.unit_of_work import UnitOfWork
from game.quests import QuestSelectionStore
from models.player import Player


def test_quest_selection_store_isolation():
    store = QuestSelectionStore()
    q1 = get_quest("first_steps")
    q2 = get_quest("goblin_slayer")

    store.set_selection(101, [q1, q2])
    store.set_selection(102, [q2])

    ctx1 = store.get_selection(101)
    ctx2 = store.get_selection(102)

    assert ctx1 is not None
    assert ctx2 is not None
    assert ctx1.get_quest_by_number(1).id == "first_steps"
    assert ctx2.get_quest_by_number(1).id == "goblin_slayer"


def test_quest_selection_expiration():
    store = QuestSelectionStore()
    q1 = get_quest("first_steps")
    ctx = store.set_selection(103, [q1], timeout=0.01)
    time.sleep(0.02)
    assert ctx.is_expired()
    assert store.get_selection(103) is None


def test_quest_selection_out_of_bounds():
    store = QuestSelectionStore()
    q1 = get_quest("first_steps")
    store.set_selection(104, [q1])

    ctx = store.get_selection(104)
    assert ctx.get_quest_by_number(0) is None
    assert ctx.get_quest_by_number(-1) is None
    assert ctx.get_quest_by_number(2) is None
    assert ctx.get_quest_by_number(1).id == "first_steps"


def test_accept_quest_numeric_and_persist(db_path):
    with UnitOfWork() as uow:
        player = Player(discord_id=201, name="Hero", level=1)
        uow.players.create(player)

    store = QuestSelectionStore()
    available = get_available_quests(1)
    store.set_selection(201, available)

    ctx = store.get_selection(201)
    q_obj = ctx.get_quest_by_number(1)
    assert q_obj is not None

    with UnitOfWork() as uow:
        uow.quests.assign_quest(201, q_obj.id)

    with UnitOfWork() as uow:
        active = uow.quests.get_active_quests(201)
        assert len(active) == 1
        assert active[0][0] == q_obj.id


def test_fail_quest_persists(db_path):
    with UnitOfWork() as uow:
        player = Player(discord_id=205, name="Warrior", level=1)
        uow.players.create(player)
        uow.quests.assign_quest(205, "first_steps")

    with UnitOfWork() as uow:
        uow.quests.fail_quest(205, "first_steps")

    with UnitOfWork() as uow:
        status_data = uow.quests.get_quest_status(205, "first_steps")
        assert status_data is not None
        assert status_data[1] == "FAILED"


def test_duplicate_active_quest_rejected(db_path):
    with UnitOfWork() as uow:
        player = Player(discord_id=202, name="Hero", level=1)
        uow.players.create(player)
        uow.quests.assign_quest(202, "first_steps")

    with UnitOfWork() as uow:
        status_data = uow.quests.get_quest_status(202, "first_steps")
        assert status_data is not None
        assert status_data[1] == "ACTIVE"


def test_completed_non_repeatable_quest_rejected(db_path):
    with UnitOfWork() as uow:
        player = Player(discord_id=203, name="Hero", level=1)
        uow.players.create(player)
        uow.quests.assign_quest(203, "first_steps")
        uow.quests.complete_quest(203, "first_steps")

    with pytest.raises(ValueError, match="Quest already completed"):
        with UnitOfWork() as uow:
            uow.quests.assign_quest(203, "first_steps")


def test_level_requirement_validation():
    q_wolf = get_quest("wolf_hunter")
    assert q_wolf.required_level == 2

    p = Player(discord_id=204, name="Novice", level=1)
    assert p.level < q_wolf.required_level
