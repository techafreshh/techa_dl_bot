# Feature: Phase 1 - Basic Setup & Local API Integration

The following plan should be complete, but its important that you validate documentation and codebase patterns and task sanity before you start implementing.

## Feature Description

Establish the baseline infrastructure for the Telegram Download Bot. This includes setting up the Docker environment with a local Telegram Bot API server, configuring the Python bot to connect to it, and verifying communication with a basic echo bot functionality.

## User Story

As a Developer,
I want to set up the bot to communicate through a local Telegram Bot API server,
So that the system is prepared to handle files up to 2GB in later phases.

## Problem Statement

Standard Telegram Bot API has a 50MB upload limit. To achieve the 2GB goal, we must route all requests through a local API server instance. This requires specific network orchestration and bot client configuration.

## Solution Statement

Deploy two Docker services: `telegram-bot-api` (official image) and `bot` (Python 3.11). Use `aiogram`'s `TelegramAPIServer` class to point the bot to the local container. Implement a shared volume to enable the "local mode" optimization for file handling.

## Feature Metadata

**Feature Type**: New Capability (Infrastructure)
**Estimated Complexity**: Medium
**Primary Systems Affected**: Docker Orchestration, Bot Initialization, Configuration Management
**Dependencies**: `aiogram`, `python-dotenv`, `docker-compose`

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `GEMINI.md` - Why: General architectural rules and project structure.
- `.gemini/PRD.md` - Why: Requirements for Phase 1 deliverables.

### New Files to Create

- `requirements.txt` - Python dependencies for Phase 1.
- `.env.example` - Template for environment variables.
- `bot/config.py` - Pydantic-style configuration loading.
- `bot/main.py` - Entry point with custom API server session.
- `Dockerfile` - Python environment for the bot.
- `docker-compose.yml` - Multi-container setup.

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Aiogram Custom Server Docs](https://docs.aiogram.dev/en/v3.27.0/api/session/custom_server.html)
  - Specific section: Using `TelegramAPIServer` and `AiohttpSession`.
- [Telegram Bot API Local Server](https://github.com/tdlib/telegram-bot-api)
  - Specific section: Command line arguments for local server (API_ID, API_HASH).

### Patterns to Follow

**Naming Conventions:**
- Environment Variables: `UPPER_SNAKE_CASE` (e.g., `TELEGRAM_API_URL`)
- Configuration Class: `Config` or `Settings`

**Bot Initialization Pattern:**
```python
session = AiohttpSession(
    api=TelegramAPIServer.from_base('http://telegram-bot-api:8081')
)
bot = Bot(token=config.BOT_TOKEN, session=session)
```

---

## IMPLEMENTATION PLAN

### Phase 1: Environment & Dependency Definition
Define the software environment and required libraries.

### Phase 2: Configuration Layer
Implement a robust way to load environment variables and ensure all required keys are present.

### Phase 3: Docker Orchestration
Setup the containers and their network/volume interdependencies.

### Phase 4: Bot Baseline (Echo)
Initialize the bot with the local API session and verify message handling.

---

## STEP-BY-STEP TASKS

### Task 1: Define Dependencies
- **CREATE**: `requirements.txt`
- **IMPLEMENT**: Add `aiogram`, `python-dotenv`.
- **VALIDATE**: `pip install -r requirements.txt`

### Task 2: Configuration Loader
- **CREATE**: `bot/config.py`
- **IMPLEMENT**: Load `BOT_TOKEN`, `ADMIN_IDS` (list), `TELEGRAM_API_URL` (default: http://telegram-bot-api:8081).
- **VALIDATE**: `python -c "from bot.config import settings; print(settings.BOT_TOKEN)"`

### Task 3: Bot Containerization
- **CREATE**: `Dockerfile`
- **IMPLEMENT**: Use `python:3.11-slim`, install requirements, copy `bot/` directory.
- **VALIDATE**: `docker build -t tg-bot .`

### Task 4: Local API & Orchestration
- **CREATE**: `docker-compose.yml`
- **IMPLEMENT**: 
    - Service `telegram-bot-api`: Use `aiogram/telegram-bot-api`, pass `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`.
    - Service `bot`: Link to `telegram-bot-api`, mount shared volume `/tmp/telegram-bot-api`.
- **VALIDATE**: `docker-compose config`

### Task 5: Echo Bot Implementation
- **CREATE**: `bot/main.py`
- **IMPLEMENT**: 
    - `AiohttpSession` with `TelegramAPIServer.from_base`.
    - Simple `message.answer(message.text)` handler.
    - Start polling.
- **VALIDATE**: `docker-compose up bot` (Verify logs show successful connection)

---

## TESTING STRATEGY

### Integration Tests
- Verify container-to-container connectivity: Bot should ping `telegram-bot-api:8081`.
- Functional Echo: Send a message to the bot and receive the same message back.

### Edge Cases
- `telegram-bot-api` service starting slower than `bot` (Use `depends_on` with healthcheck or simple retry logic in bot).
- Missing environment variables (Config should raise a clear error).

---

## VALIDATION COMMANDS

### Level 1: Configuration
- `python -m bot.config` (if a print test is added)

### Level 2: Docker
- `docker-compose ps` (All services should be `Up`)
- `docker-compose logs bot` (Check for "Bot started" or similar log)

### Level 3: Manual
- Send `/start` to your bot on Telegram. If it replies, Phase 1 is successful.

---

## ACCEPTANCE CRITERIA

- [ ] `docker-compose up` starts both services without immediate crashes.
- [ ] Bot logs confirm it is using the local API URL.
- [ ] Bot successfully replies to messages (Echo functionality).
- [ ] Environment variables are correctly validated at startup.

---

## COMPLETION CHECKLIST

- [ ] All files created.
- [ ] Docker services linked and healthy.
- [ ] Echo functionality verified.
- [ ] Config handles missing keys gracefully.
