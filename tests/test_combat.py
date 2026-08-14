from __future__ import annotations

import time
import pytest

from game.combat import calculate_damage, execute_turn, resolve_combat
from models.enemy import Enemy
from models.player import Player


def test_calculate_damage_floor():
    dmg = calculate_damage(attack=5, defense=20, is_crit=False)
    assert dmg >= 1


def test_calculate_damage_critical_multiplier():
    dmg_normal = calculate_damage(attack=20, defense=10, is_crit=False)
    dmg_crit = calculate_damage(attack=20, defense=10, is_crit=True)
    assert dmg_crit > dmg_normal


def test_execute_turn_attack_reduces_hp(sample_player, sample_enemy):
    init_enemy_hp = sample_enemy.hp
    res = execute_turn(sample_player, sample_enemy, action="attack")
    assert sample_enemy.hp < init_enemy_hp
    assert res.player_damage_dealt > 0


def test_execute_turn_flee_success(sample_player, sample_enemy):
    res = execute_turn(sample_player, sample_enemy, action="flee")
    assert len(res.log_messages) > 0


def test_resolve_combat_player_victory(sample_player, sample_enemy):
    sample_player.attack = 50
    summary = resolve_combat(sample_player, sample_enemy)
    assert summary.winner == "player"
    assert summary.xp_reward == sample_enemy.xp_reward
    assert summary.gold_reward == sample_enemy.gold_reward
    assert len(summary.drops) > 0


def test_execute_turn_on_dead_player_fails(sample_enemy):
    dead_player = Player(discord_id=999, name="DeadHero", hp=0)
    with pytest.raises(ValueError, match="Combatant is defeated"):
        execute_turn(dead_player, sample_enemy, action="attack")


def test_execute_turn_on_dead_enemy_fails(sample_player):
    dead_enemy = Enemy(
        id="dead",
        name="Ghost",
        level=1,
        hp=0,
        max_hp=30,
        attack=5,
        defense=2,
        xp_reward=10,
        gold_reward=5,
    )
    with pytest.raises(ValueError, match="Combatant is defeated"):
        execute_turn(sample_player, dead_enemy, action="attack")


def test_execute_turn_invalid_action_fails(sample_player, sample_enemy):
    with pytest.raises(ValueError, match="Unknown combat action"):
        execute_turn(sample_player, sample_enemy, action="dance")


def test_combat_simulation_benchmark(sample_player, sample_enemy):
    start = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        p = Player(discord_id=1, name="Hero", hp=100, max_hp=100, attack=20, defense=5)
        e = Enemy(
            id="e",
            name="Mob",
            level=1,
            hp=50,
            max_hp=50,
            attack=10,
            defense=2,
            xp_reward=10,
            gold_reward=5,
        )
        resolve_combat(p, e)
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0
