# DiscordTextRPG

A persistent, text-based Discord RPG bot built with Python, discord.py, and SQLite. Features an interactive button-based Discord UI, turn-based combat, quest tracking, dynamic equipment management, and persistent player progression.

## Features

- **Turn-Based Combat**: Fight wild enemies with interactive attack, defend, heal, and flee actions.
- **Quest System**: Discover, accept, track, and complete location-based quests with combat initiation and gold/XP rewards.
- **Button-Based Discord UI**: Fully interactive Discord button Views across all game states (exploration, profile, inventory, shop, and combat).
- **Dynamic Equipment System**: Equip weapons, armor, and accessories (`ACCESSORY_1`, `ACCESSORY_2`) with effective stat calculation (Base Stats + Equipment Bonuses).
- **Shop & Economy**: Buy consumable items and equipment from the merchant shop, sell loot, and earn gold from battles and quests.
- **Player Progression & Rest**: XP leveling system, stat progression, and inn resting to recover health.
- **Persistent Storage**: Full SQLite WAL-mode persistence for player profiles, inventory items, active quests, and equipment loadouts.

## Tech Stack

- **Language**: Python 3.11+
- **Discord API**: discord.py (Commands & UI Components)
- **Database**: SQLite (WAL Mode)
- **Environment Management**: python-dotenv
- **Testing**: pytest (Unit & Integration)
- **Dev Reloading**: hupper

## Project Structure


DiscordTextRPG/

├── cogs/

├── config/

├── data/

├── database/

├── game/

├── models/

├── storage/

├── tests/

├── ui/

├── utils/

├── bot.py

├── pyproject.toml

└── requirements.txt

## Local Development

For complete local environment setup instructions, virtual environment configuration, database details, and troubleshooting, see [local_development.md](local_development.md).

## Quick Start

1. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   env
   DISCORD_TOKEN=your_discord_bot_token_here
   

2. **Run Tests**:
   pytest
   pytest -v
   

3. **Run the Bot (with Auto-Reloading)**:
   hupper -m bot
   
   Or run standard startup without auto-reload:
   python bot.py
   

## Environment Variables

|     Variable    |                   Description                   | Required |
| --------------- | ----------------------------------------------- | -------- |
| `DISCORD_TOKEN` | Discord Bot Token from Discord Developer Portal |   Yes    |

## Git & Security Notes

- Local SQLite database files (`storage/game.db`) and secrets (`.env`) are ignored by `.gitignore` to prevent sensitive credentials and local game state from being committed.
- Schema definitions (`database/schema_initializer.py`) and static game registries (`data/`) are tracked to allow fresh environment replication.
