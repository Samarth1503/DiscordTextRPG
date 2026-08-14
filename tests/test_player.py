from database.repositories.player_repository import PlayerRepository
from models.player import Player


def test_player_defaults():
    player = Player(
        discord_id=123456789,
        name="Arthur",
    )

    assert player.discord_id == 123456789
    assert player.name == "Arthur"
    assert player.level == 1
    assert player.experience == 0
    assert player.hp == 100
    assert player.max_hp == 100
    assert player.attack == 10
    assert player.defense == 5
    assert player.gold == 0


def test_player_can_be_modified():
    player = Player(
        discord_id=123456789,
        name="Arthur",
    )

    player.level = 2
    player.experience = 100
    player.hp = 120
    player.max_hp = 120
    player.attack = 15
    player.defense = 8
    player.gold = 250

    assert player.level == 2
    assert player.experience == 100
    assert player.hp == 120
    assert player.max_hp == 120
    assert player.attack == 15
    assert player.defense == 8
    assert player.gold == 250


def test_player_persists_changes(repository: PlayerRepository):
    player = Player(
        discord_id=123456789,
        name="Arthur",
    )

    repository.create(player)

    player.level = 2
    player.experience = 100
    player.gold = 250

    repository.update(player)

    saved_player = repository.get_by_discord_id(123456789)

    assert saved_player is not None
    assert saved_player.level == 2
    assert saved_player.experience == 100
    assert saved_player.gold == 250
