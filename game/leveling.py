from __future__ import annotations

import math
from dataclasses import dataclass

BASE_XP = 100
XP_GROWTH = 50


@dataclass(slots=True)
class LevelUpResult:
    new_experience: int
    new_level: int
    levels_gained: int


def experience_required_for_level(level: int) -> int:
    if level < 1:
        raise ValueError("Level must be at least 1.")

    return BASE_XP + ((level - 1) * XP_GROWTH)


def total_experience_for_level(level: int) -> int:
    if level < 1:
        raise ValueError("Level must be at least 1.")
    if level == 1:
        return 0

    return 25 * (level - 1) * (level + 2)


def calculate_level(experience: int) -> int:
    if experience < 0:
        raise ValueError("Experience cannot be negative.")

    if experience == 0:
        return 1

    discriminant = 9.0 + (4.0 * experience / 25.0)
    level = math.floor((-1.0 + math.sqrt(discriminant)) / 2.0)
    return max(1, level)


def experience_to_next_level(experience: int) -> int:
    if experience < 0:
        raise ValueError("Experience cannot be negative.")

    current_lvl = calculate_level(experience)
    next_lvl_total_xp = total_experience_for_level(current_lvl + 1)
    return next_lvl_total_xp - experience


def add_experience(
    current_experience: int,
    amount: int,
) -> tuple[int, int]:
    if current_experience < 0:
        raise ValueError("Experience cannot be negative.")

    if amount < 0:
        raise ValueError("Experience amount cannot be negative.")

    new_experience = current_experience + amount
    new_level = calculate_level(new_experience)

    return new_experience, new_level
