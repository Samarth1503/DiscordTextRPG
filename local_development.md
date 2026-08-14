# Local Development Guide

This guide explains how to set up, configure, develop, test, and run the `DiscordTextRPG` project on a local machine from a fresh clone.


## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.11+**: Check version with `python --version` or `python3 --version`.
- **Git**: For source control management.
- **Discord Bot Application & Token**: A bot application created in the [Discord Developer Portal](https://discord.com/developers/applications).
  - Ensure **Message Content Intent** is enabled under the Bot settings.


## 1. Clone the Repository

Clone the repository and navigate into the project directory:

git clone <repository-url>
cd DiscordTextRPG


## 2. Create a Virtual Environment

Create and activate an isolated Python virtual environment:

### Windows (PowerShell)
powershell
python -m venv venv
.\venv\Scripts\activate

### Windows (Command Prompt)
cmd
python -m venv venv
venv\Scripts\activate.bat

### Linux / macOS

python3 -m venv venv
source venv/bin/activate


## 3. Install Dependencies

Install required dependencies listed in `requirements.txt`:

pip install -r requirements.txt


## 4. Environment Configuration

1. Create a `.env` file in the root `DiscordTextRPG/` directory:

env
DISCORD_TOKEN=your_discord_bot_token_here


2. **Security Note**: Never commit `.env` to Git. It is listed in `.gitignore` and contains sensitive bot credentials.


## 5. Database Setup

- **Storage Location**: SQLite database is stored locally at `storage/game.db`.
- **Automatic Initialization**: You do **not** need to manually create database files or run manual SQL scripts. On startup, `database/schema_initializer.py` automatically initializes tables, indexes, and static item data if the database does not exist.
- **WAL Mode**: SQLite operates in Write-Ahead Logging (WAL) mode for fast concurrent reads and writes.
- **Git Exclusion**: `storage/game.db` and SQLite WAL/journal files are ignored by Git to preserve developer state isolation.


## 6. Running the Bot

### Development Mode (with Auto-Reloading)
Run `hupper` to monitor python files for changes and automatically reload the bot process:

hupper -m bot

### Standard Mode (without Auto-Reloading)

python bot.py


## 7. Running Tests

Run the test suite using `pytest`:

# Run all unit and integration tests
pytest

# Run tests in verbose mode
pytest -v

# Run a specific test file
pytest tests/unit/test_equipment_bug_fix.py -v


## 8. Recommended Development Workflow

1. Activate your virtual environment: `.\venv\Scripts\activate` (or `source venv/bin/activate`).
2. Pull latest changes: `git pull origin main`.
3. Update dependencies: `pip install -r requirements.txt`.
4. Verify environment configuration in `.env`.
5. Run the test suite: `pytest`.
6. Start the bot: `hupper -m bot`.
7. Make code edits (Hupper automatically reloads the process upon saving).
8. Re-run tests before committing: `pytest -v`.


## 9. Troubleshooting

### 1. Missing `.env` File or `DISCORD_TOKEN`
- **Symptom**: `ValueError: DISCORD_TOKEN is missing in environment variables.`
- **Fix**: Create a `.env` file in the root folder containing `DISCORD_TOKEN=your_token`.

### 2. Invalid Token / Gateway Privileged Intents Error
- **Symptom**: `discord.errors.LoginFailure` or `PrivilegedIntentsRequired`.
- **Fix**: Verify your token in Discord Developer Portal. Ensure **Message Content Intent** is toggled ON under Bot settings.

### 3. Module Import Errors
- **Symptom**: `ModuleNotFoundError: No module named 'discord'` or `No module named 'hupper'`.
- **Fix**: Ensure your virtual environment is active and run `pip install -r requirements.txt`.

### 4. Database File Locks (Windows)
- **Symptom**: `sqlite3.OperationalError: database is locked`.
- **Fix**: Ensure only one bot instance is running. If necessary, close active Python processes or restart your terminal.
