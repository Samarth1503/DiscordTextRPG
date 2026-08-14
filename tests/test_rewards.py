from __future__ import annotations

import time
import pytest

from game.rewards import apply_rewards
from models.player import Player


def test_apply_rewards_xp_and_gold(sample_player):
    summary = apply_rewards(sample_player, xp=50, gold=25)
    assert sample_player.experience == 50
    assert sample_player.gold == 125
    assert summary.levels_gained == 0


def test_apply_rewards_triggers_level_up(sample_player):
    old_max_hp = sample_player.max_hp
    old_attack = sample_player.attack
    summary = apply_rewards(sample_player, xp=150, gold=50)

    assert sample_player.level == 2
    assert summary.levels_gained == 1
    assert sample_player.max_hp > old_max_hp
    assert sample_player.attack > old_attack


def test_apply_rewards_drops_included(sample_player):
    drops = [("health_potion", 2)]
    summary = apply_rewards(sample_player, xp=10, gold=10, drops=drops)
    assert ("health_potion", 2) in summary.drops


def test_apply_negative_xp_reward_fails(sample_player):
    with pytest.raises(ValueError, match="Rewards cannot be negative"):
        apply_rewards(sample_player, xp=-50, gold=10)


def test_apply_negative_gold_reward_fails(sample_player):
    with pytest.raises(ValueError, match="Rewards cannot be negative"):
        apply_rewards(sample_player, xp=50, gold=-10)


def test_rewards_performance_benchmark(sample_player):
    start = time.perf_counter()
    for _ in range(10000):
        p = Player(discord_id=1, name="Hero")
        apply_rewards(p, xp=25, gold=10)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.2  # 10,000 reward applications in < 200ms
