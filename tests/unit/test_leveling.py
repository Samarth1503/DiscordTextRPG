from game.leveling import (
    add_experience,
    calculate_level,
    experience_required_for_level,
    experience_to_next_level,
)


def test_first_level_requires_100_experience():
    assert experience_required_for_level(1) == 100


def test_second_level_requires_150_experience():
    assert experience_required_for_level(2) == 150


def test_invalid_level_is_rejected():
    try:
        experience_required_for_level(0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_level_one_at_zero_experience():
    assert calculate_level(0) == 1


def test_level_two_at_100_experience():
    assert calculate_level(100) == 2


def test_level_three_at_250_experience():
    assert calculate_level(250) == 3


def test_experience_to_next_level():
    assert experience_to_next_level(25) == 75


def test_add_experience():
    experience, level = add_experience(75, 25)

    assert experience == 100
    assert level == 2


def test_negative_experience_is_rejected():
    try:
        calculate_level(-1)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_negative_experience_reward_is_rejected():
    try:
        add_experience(100, -10)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")
