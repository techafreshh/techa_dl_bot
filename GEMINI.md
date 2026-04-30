# GEMINI.md

This file provides guidance to Gemini CLI when working with code in this repository.

## Project Overview

A specialized Telegram Bot designed to download files up to 2GB from user-provided URLs and subsequently upload them to a designated Telegram group. It leverages a local Telegram Bot API server to bypass the standard 50MB file size limits and uses an asyncio queue to handle multiple concurrent downloads.

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.11+ | Primary programming language |
| aiogram v3 | Asynchronous Telegram Bot framework |
| aiohttp | Async HTTP client for chunked file downloading |
| Docker & Docker Compose | Containerization for the bot and Local Bot API Server |

---

## Commands

```bash
# Development (Virtual Environment Setup)
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally (requires running bot api server)
python bot/main.py

# Docker Build & Run
docker-compose up --build -d
```

---

## Project Structure

```
telegram-download-bot/
├── bot/
│   ├── main.py           # Entry point, bot setup and polling
│   ├── config.py         # Environment variables and configuration
│   ├── handlers.py       # Telegram message handlers
│   └── downloader.py     # aiohttp download logic and queue management
├── docker-compose.yml    # Runs bot and local API server together
├── Dockerfile            # Bot container definition
├── requirements.txt      # Python dependencies
└── .env                  # Sensitive configuration (Not committed)
```

---

## Architecture

- **Concurrent Producer-Consumer:** Incoming links from admins are pushed to an `asyncio.Queue`. Background worker tasks pull from the queue to process downloads and uploads, strictly limiting concurrency (e.g., 5 concurrent tasks).
- **Chunked Processing:** Files are downloaded in chunks directly to the disk (`/tmp/downloads`) using `aiohttp` to maintain a low memory footprint.
- **Local API Integration:** The bot connects to a locally hosted Telegram API server container to upload files up to 2GB. Both containers share a file volume to use local paths directly.

---

## Code Patterns

### Naming Conventions
- **Variables/Functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE` (especially in `config.py`)

### Error Handling
- Use `try/except/finally` blocks extensively, especially to ensure that temporary downloaded files are deleted in the `finally` block to prevent disk space exhaustion.
- Catch `aiohttp.ClientError` for download failures and `TelegramAPIError` for upload failures.

### Asynchronous Operations
- NEVER use blocking I/O (like `requests` or `open()` without a threadpool/aiofiles) in the main bot loop.
- Use `asyncio.sleep()` for non-blocking delays.

---

## Validation

Commands to run before committing (Assuming `black` and `flake8` or `ruff` are adopted):

```bash
# Format code
black bot/
# Lint code
ruff check bot/
```

---

## Key Files

| File | Purpose |
|------|---------|
| `bot/main.py` | Bot initialization and event loop |
| `bot/downloader.py` | Core chunked downloading and queue management |
| `docker-compose.yml` | Architecture definition linking the bot and the API server |

---

## Notes

- **Rate Limits:** Throttle progress message updates (e.g., every 5 seconds) to avoid `FloodWait` errors from Telegram.
- **Security:** Do not commit `.env`. Ensure that the `ADMIN_IDS` check is strictly enforced in the message handlers.
- **Resource Management:** Always clean up files from the VPS disk as soon as the upload completes or fails.