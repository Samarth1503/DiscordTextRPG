from __future__ import annotations

import random
from dataclasses import dataclass, field

from models.enemy import Enemy
from models.player import Player


@dataclass(slots=True)
class CombatContext:
    enemy: Enemy
    source: str = "exploration"
    quest_id: str | None = None


@dataclass(slots=True)
class TurnResult:
    player_hp: int
    enemy_hp: int
    player_damage_dealt: int
    enemy_damage_dealt: int
    is_player_crit: bool
    is_enemy_crit: bool
    log_messages: list[str]


@dataclass(slots=True)
class CombatSummary:
    winner: str
    total_turns: int
    xp_reward: int = 0
    gold_reward: int = 0
    drops: list[tuple[str, int]] = field(default_factory=list)
    log: list[str] = field(default_factory=list)


def calculate_damage(attack: int, defense: int, is_crit: bool = False) -> int:
    base_damage = max(1, attack - (defense // 2))
    if is_crit:
        base_damage = int(base_damage * 1.5)
    variance = random.uniform(0.9, 1.1)
    damage = max(1, int(base_damage * variance))
    return damage


def roll_critical(crit_chance: float = 0.1) -> bool:
    return random.random() <= crit_chance


def execute_turn(
    player: Player,
    enemy: Enemy,
    action: str = "attack",
    effective_attack: int | None = None,
    effective_defense: int | None = None,
) -> TurnResult:
    if not player.is_alive():
        raise ValueError("Combatant is defeated.")
    if not enemy.is_alive():
        raise ValueError("Combatant is defeated.")

    p_atk = effective_attack if effective_attack is not None else player.attack
    p_def = effective_defense if effective_defense is not None else player.defense

    log: list[str] = []
    p_damage = 0
    e_damage = 0
    p_crit = False
    e_crit = False

    if action == "attack":
        p_crit = roll_critical(0.1)
        p_damage = calculate_damage(p_atk, enemy.defense, p_crit)
        actual_p_dmg = enemy.take_damage(p_damage)
        crit_str = " **CRITICAL HIT!**" if p_crit else ""
        log.append(
            f"⚔️ **{player.name}** attacks **{enemy.name}** for **{actual_p_dmg}** damage!{crit_str}"
        )

        if enemy.is_alive():
            e_crit = roll_critical(0.05)
            e_damage = calculate_damage(enemy.attack, p_def, e_crit)
            actual_e_dmg = player.take_damage(e_damage)
            e_crit_str = " **CRITICAL HIT!**" if e_crit else ""
            log.append(
                f"👹 **{enemy.name}** counter-attacks **{player.name}** for **{actual_e_dmg}** damage!{e_crit_str}"
            )
        else:
            log.append(f"💀 **{enemy.name}** has been defeated!")
    elif action == "flee":
        if random.random() <= 0.5:
            log.append(f"🏃 **{player.name}** successfully fled from combat!")
        else:
            log.append(f"❌ **{player.name}** failed to flee!")
            e_crit = roll_critical(0.05)
            e_damage = calculate_damage(enemy.attack, p_def, e_crit)
            actual_e_dmg = player.take_damage(e_damage)
            log.append(
                f"👹 **{enemy.name}** strikes fleeing **{player.name}** for **{actual_e_dmg}** damage!"
            )
    else:
        raise ValueError(f"Unknown combat action '{action}'.")

    return TurnResult(
        player_hp=player.hp,
        enemy_hp=enemy.hp,
        player_damage_dealt=p_damage,
        enemy_damage_dealt=e_damage,
        is_player_crit=p_crit,
        is_enemy_crit=e_crit,
        log_messages=log,
    )


def resolve_combat(player: Player, enemy: Enemy) -> CombatSummary:
    turns = 0
    full_log: list[str] = []

    while player.is_alive() and enemy.is_alive():
        turns += 1
        turn_res = execute_turn(player, enemy, action="attack")
        full_log.extend(turn_res.log_messages)

    if player.is_alive() and not enemy.is_alive():
        drops = enemy.roll_loot()
        return CombatSummary(
            winner="player",
            total_turns=turns,
            xp_reward=enemy.xp_reward,
            gold_reward=enemy.gold_reward,
            drops=drops,
            log=full_log,
        )
    else:
        return CombatSummary(
            winner="enemy",
            total_turns=turns,
            xp_reward=0,
            gold_reward=0,
            drops=[],
            log=full_log,
        )
