# Product Requirements Document (PRD): Telegram Download & Target Group Upload Bot

## 1. Executive Summary
This document outlines the requirements for a specialized Telegram Bot designed to download files from user-provided URLs and subsequently upload them to a designated Telegram group. To handle files up to 2GB in size, the bot will utilize the Local Telegram Bot API server. 

The core value proposition is to automate the bridging of large file downloads directly into a Telegram community without requiring the administrator to manually download and upload the files on their personal device. The MVP will focus on a stable, concurrent queue-based system hosted on a VPS.

## 2. Mission
**Mission Statement:** To provide a seamless, high-capacity file transfer bridge from the web into a Telegram group.
**Core Principles:**
- **Reliability:** File transfers must resume or fail gracefully without crashing the bot.
- **Performance:** Low memory footprint using chunked streaming and concurrent limits.
- **Transparency:** Clear progress reporting to the user during long-running tasks.

## 3. Target Users
- **Primary Persona:** Telegram Group Administrator.
- **Technical Comfort Level:** Comfortable with VPS hosting and basic Docker setup, but wants the bot usage to be simple (just paste a link).
- **Key User Needs & Pain Points:**
  - Standard Telegram bots cannot upload files larger than 50MB.
  - Manual downloading/uploading of large files consumes personal bandwidth and time.
  - Needs to queue multiple downloads without overwhelming the server.

## 4. MVP Scope
### In Scope
- ✅ Processing standard HTTP/HTTPS download links.
- ✅ Downloading files directly to VPS storage in chunks.
- ✅ Bypassing the 50MB limit by supporting up to 2GB files via Local Bot API.
- ✅ Uploading downloaded files to a specified target Telegram group.
- ✅ Concurrency control (maximum 5 concurrent downloads).
- ✅ Asynchronous queuing for links received beyond the concurrent limit.
- ✅ Progress messages for both downloading and uploading phases.
- ✅ Restricting access to a hardcoded/configured list of Admin User IDs.
- ✅ Dockerized deployment including the Local Bot API server.

### Out of Scope
- ❌ Supporting torrents, magnet links, or specialized protocols (e.g., FTP).
- ❌ Extracting/unzipping archives before upload.
- ❌ Customizing target groups per link (hardcoded target group for MVP).
- ❌ Resuming interrupted downloads if the bot restarts.
- ❌ Paid/freemium user tiers.

## 5. User Stories
1. **As an Admin,** I want to send a URL to the bot, so that the bot downloads the file on the VPS instead of my device.
2. **As an Admin,** I want the bot to upload the file to our target group up to 2GB, so that I can share large files with the community.
3. **As an Admin,** I want to see a progress bar for the download and upload, so that I know the bot is not stalled.
4. **As an Admin,** I want to queue multiple links at once, so that I can batch requests without waiting for one to finish.
5. **As a system operator,** I want unauthorized users to be ignored, so that strangers cannot abuse my VPS bandwidth.

## 6. Core Architecture & Patterns
- **High-Level Architecture:**
  - **Bot Container:** Python `aiogram` v3 application handling messages, orchestrating downloads/uploads, and managing the `asyncio.Queue`.
  - **Local Bot API Server Container:** Official Telegram API image to handle the large file limit overrides (2GB).
  - **Shared Volume:** A shared Docker volume `/tmp/downloads` between the bot and the API server to allow local file passing (`file://` protocol).
- **Concurrency Pattern:** A producer-consumer pattern where incoming links are pushed to an `asyncio.Queue`, and 5 concurrent worker tasks pull from the queue to process downloads/uploads.
- **Directory Structure:**
  ```
  telegram-download-bot/
  ├── bot/
  │   ├── main.py
  │   ├── config.py
  │   ├── handlers.py
  │   ├── downloader.py
  │   └── requirements.txt
  ├── docker-compose.yml
  ├── Dockerfile
  └── .env
  ```

## 7. Tools/Features
- **Message Listener:** Checks if the sender is an authorized admin. Validates if the message is a URL.
- **Download Engine:** Uses `aiohttp` to stream the file to disk. Calculates total size and updates the Telegram progress message periodically (e.g., every 5-10 seconds to avoid rate limits).
- **Upload Engine:** Uses `aiogram`'s local file sending capability via the Local Bot API server to push the file to the target group.
- **Queue Manager:** Limits active workers to 5. Notifies the user of queue position.
- **Cleanup Routine:** Deletes the local file immediately after a successful or failed upload to maintain VPS storage capacity.

## 8. Technology Stack
- **Language:** Python 3.11+
- **Bot Framework:** `aiogram` v3 (async Telegram framework)
- **HTTP Client:** `aiohttp` (for chunked async downloading)
- **Deployment:** Docker & Docker Compose
- **Telegram Local API:** Official `aiogram/telegram-bot-api` Docker image.

## 9. Security & Configuration
- **Authentication:** Only Telegram User IDs specified in the `ADMIN_IDS` environment variable will be processed.
- **Configuration Management:** All sensitive variables loaded via `.env`:
  - `BOT_TOKEN`
  - `ADMIN_IDS` (comma-separated list)
  - `TARGET_GROUP_ID`
  - `API_ID` & `API_HASH` (required for Local Bot API Server)
- **Security Scope:**
  - ✅ In-scope: Ignoring messages from non-admins, preventing path traversal during downloads.
  - ❌ Out-of-scope: Rate limiting admins (trusted users).

## 10. API Specification
*Not applicable for MVP as this is a Telegram bot without an external REST API.*

## 11. Success Criteria
- ✅ The bot successfully authenticates admins and ignores others.
- ✅ The bot can download a file up to 2GB from a direct URL.
- ✅ The bot can upload the 2GB file to the target Telegram group.
- ✅ The bot properly queues a 6th link when 5 downloads are already running.
- ✅ Progress messages update correctly without hitting Telegram rate limits (FloodWait).
- ✅ Temporary files are reliably deleted after processing.

## 12. Implementation Phases
**Phase 1: Basic Setup & Local API Integration**
- Goal: Get the bot running with the Local Bot API server.
- Deliverables: ✅ Docker Compose setup, ✅ Basic echo bot using local API.
- Validation: Bot responds to messages and is confirmed to route through the local API container.

**Phase 2: Core Download/Upload Logic**
- Goal: Implement file downloading and target group uploading.
- Deliverables: ✅ `aiohttp` chunked downloader, ✅ Upload logic, ✅ Progress bar updates.
- Validation: Successfully download and upload a 100MB file.

**Phase 3: Concurrency & Queueing**
- Goal: Implement the 5-concurrent-download limit.
- Deliverables: ✅ `asyncio.Queue` integration, ✅ 5 background worker tasks.
- Validation: Send 10 links rapidly; 5 start immediately, 5 wait in queue.

**Phase 4: Security, Cleanup & Polish**
- Goal: Add access control and ensure storage is managed.
- Deliverables: ✅ Admin ID filtering, ✅ File deletion post-upload, ✅ Error handling (e.g., invalid links, network drops).
- Validation: Non-admins are ignored. Disk space remains constant after full processing cycles.

## 13. Future Considerations
- Supporting YouTube/media extraction (e.g., via `yt-dlp`).
- Extracting ZIP/RAR files before uploading.
- Supporting multiple target groups selectable via an inline keyboard.

## 14. Risks & Mitigations
1. **Risk:** Telegram FloodWait rate limits from updating progress messages too often.
   **Mitigation:** Throttle progress message updates to a maximum of once every 5 seconds.
2. **Risk:** VPS running out of disk space with concurrent huge files (5 * 2GB = 10GB).
   **Mitigation:** Ensure strict cleanup in `finally` blocks in Python. Log warnings if disk space gets low.
3. **Risk:** Direct download URLs blocking scraper User-Agents.
   **Mitigation:** Use a standard browser User-Agent in `aiohttp` requests.

## 15. Appendix
- Telegram Bot API Documentation: https://core.telegram.org/bots/api
- Aiogram Documentation: https://docs.aiogram.dev/
- Local Bot API Server Docs: https://github.com/tdlib/telegram-bot-api
