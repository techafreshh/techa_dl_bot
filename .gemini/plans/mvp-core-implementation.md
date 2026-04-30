# Feature: Telegram Download Bot MVP

The following plan should be complete, but its important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Implementation of a specialized Telegram Bot that downloads files up to 2GB from direct URLs using `aiohttp` and uploads them to a target group via a local Telegram Bot API server. It features a concurrent worker system (limit: 5) to handle multiple requests efficiently.

## User Story

As a Telegram Group Admin,
I want to send a download link to the bot,
So that the bot automatically downloads the file to its VPS and uploads it to my group, bypassing standard size limits.

## Problem Statement

Telegram's standard Bot API limits uploads to 50MB. Large files (up to 2GB) require a local Bot API server. Admins also need a way to queue multiple downloads without manual intervention or bandwidth consumption.

## Solution Statement

Deploy a Dockerized system with:
1. A local Telegram Bot API server container.
2. A Python bot container using `aiogram` v3 and `aiohttp`.
3. An `asyncio.Queue` based worker pool to limit concurrent downloads.
4. Chunked streaming to disk to keep memory usage low.

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: High
**Primary Systems Affected**: Bot Scaffolding, Downloader, Local API Integration, Docker Deployment
**Dependencies**: `aiogram`, `aiohttp`, `python-dotenv`, `docker`

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

*Note: The project is currently empty. These references point to intended locations or documentation.*

- `GEMINI.md` - Why: Contains project-wide architectural mandates and patterns.
- `.gemini/PRD.md` - Why: Detailed requirements and success criteria.

### New Files to Create

- `bot/main.py` - Bot entry point and initialization.
- `bot/config.py` - Configuration and environment variable loading.
- `bot/handlers.py` - Telegram message handlers for processing links.
- `bot/downloader.py` - Core logic for chunked downloading and queue management.
- `docker-compose.yml` - Orchestration for bot and local API server.
- `Dockerfile` - Container definition for the bot.
- `requirements.txt` - Python dependencies.
- `.env` - Environment variables (Token, Admin IDs, etc.).

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Aiogram v3 Local API Server](https://docs.aiogram.dev/en/v3.27.0/api/session/custom_server.html)
  - Specific section: Using `TelegramAPIServer` and `AiohttpSession`.
  - Why: Required to bypass 50MB upload limit.
- [Aiohttp Streaming Downloads](https://docs.aiohttp.org/en/stable/client_quickstart.html#streaming-response-content)
  - Specific section: `iter_chunked`.
  - Why: Essential for low-memory 2GB downloads.
- [Asyncio Queue Worker](https://docs.python.org/3/library/asyncio-queue.html#examples)
  - Why: Implementation pattern for concurrent download tasks.

### Patterns to Follow

**Naming Conventions:**
- Functions/Variables: `snake_case` (e.g., `download_file`, `progress_msg`)
- Classes: `PascalCase` (e.g., `DownloadWorker`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_CONCURRENT_DOWNLOADS`)

**Error Handling:**
- Use `try/except/finally` to ensure file cleanup using `os.remove()` or `pathlib.Path.unlink()`.
- Specific exceptions: `aiohttp.ClientError`, `aiogram.exceptions.TelegramAPIError`.

**Logging Pattern:**
- Use standard `logging` module.
- Log every download start, completion, and error.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Setup the environment, configuration, and Docker orchestration.

**Tasks:**
- Create `requirements.txt` with `aiogram`, `aiohttp`, `python-dotenv`.
- Implement `bot/config.py` to load and validate `.env` variables.
- Create `docker-compose.yml` with the local API server and bot container.
- Create `Dockerfile` for the Python bot.

### Phase 2: Core Download/Upload Logic

Implement the "Happy Path" for a single file transfer.

**Tasks:**
- Implement `bot/downloader.py` with a chunked download function using `aiohttp`.
- Integrate progress reporting (percentage and speed) into the downloader.
- Implement the upload logic in `bot/main.py` using `FSInputFile` and local API server mode.

### Phase 3: Queue & Concurrency

Implement the background worker pool.

**Tasks:**
- Setup `asyncio.Queue` in `bot/downloader.py`.
- Create background worker tasks (default: 5) that consume from the queue.
- Implement the handler in `bot/handlers.py` to push validated URLs to the queue.

### Phase 4: Security & Polish

Add access control and finalize error handling.

**Tasks:**
- Implement `ADMIN_IDS` check in handlers.
- Add robust cleanup logic to delete files in all scenarios.
- Refine progress messages to be throttled (max every 5s).

---

## STEP-BY-STEP TASKS

### Task 1: Initialize Project Scaffolding

- **CREATE**: `requirements.txt`
- **IMPLEMENT**: Add `aiogram`, `aiohttp`, `python-dotenv`.
- **VALIDATE**: `pip install -r requirements.txt` (local check)

### Task 2: Environment & Configuration

- **CREATE**: `bot/config.py`
- **IMPLEMENT**: Load `BOT_TOKEN`, `ADMIN_IDS`, `TARGET_GROUP_ID`, `API_ID`, `API_HASH` from environment.
- **VALIDATE**: `python -c "from bot import config; print('Config loaded')"`

### Task 3: Docker & Local API Setup

- **CREATE**: `docker-compose.yml`
- **IMPLEMENT**: Setup `aiogram/telegram-bot-api` service and bot service with shared volume `/tmp/downloads`.
- **VALIDATE**: `docker-compose config`

### Task 4: Chunked Downloader Implementation

- **CREATE**: `bot/downloader.py`
- **IMPLEMENT**: `async def download_file(url, path, progress_callback)` using `aiohttp.ClientSession` and `iter_chunked`.
- **VALIDATE**: Create a temporary script to test downloading a small file.

### Task 5: Bot Initialization with Local API

- **CREATE**: `bot/main.py`
- **IMPLEMENT**: Initialize `Bot` with `AiohttpSession(api=TelegramAPIServer.from_base(...))`. Start queue workers.
- **VALIDATE**: `python bot/main.py` (should connect and idle if token is valid)

### Task 6: Message Handlers & Admin Check

- **CREATE**: `bot/handlers.py`
- **IMPLEMENT**: Handle text messages, validate URL, check `ADMIN_IDS`.
- **VALIDATE**: Send a link to the bot (locally or via Docker).

### Task 7: Queue Integration

- **UPDATE**: `bot/downloader.py`
- **IMPLEMENT**: `QueueManager` class with background worker loop.
- **VALIDATE**: Send 6 links and verify 5 start while 1 stays in "Queued" state.

---

## TESTING STRATEGY

### Unit Tests
- Test `config.py` validation logic.
- Mock `aiohttp` response to test chunked download writer.

### Integration Tests
- End-to-end download and upload using a small file (e.g., 1MB) through the local API server.
- Verify file cleanup in `finally` blocks.

### Edge Cases
- Invalid URL (404, 500 from server).
- File size > 2GB (should be rejected or handled gracefully).
- Bot restart (Queue state will be lost, acceptable for MVP).
- Disk full scenario (aiohttp should catch `OSError`).

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
- `black bot/`
- `ruff check bot/`

### Level 2: Core Downloader
- `python -m pytest tests/test_downloader.py`

### Level 3: Integration
- `docker-compose up --build`
- Monitor logs: `docker-compose logs -f bot`

---

## ACCEPTANCE CRITERIA

- [ ] Bot starts and connects to local API server without errors.
- [ ] Only authorized admins can trigger downloads.
- [ ] Files up to 2GB are successfully downloaded to `/tmp/downloads`.
- [ ] Progress messages update with percentage and estimated time.
- [ ] Files are uploaded to the `TARGET_GROUP_ID`.
- [ ] Local files are deleted after upload/failure.
- [ ] Concurrency is limited to 5 concurrent tasks.
