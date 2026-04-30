# 🚀 Telegram Large File Downloader Bot

A specialized Telegram Bot built with **Python 3.11** and **aiogram v3** designed to download files up to **2GB** from any direct URL and upload them automatically to a designated Telegram group.

By leveraging a **Local Telegram Bot API server**, this bot bypasses the standard 50MB upload limit imposed by the Telegram cloud servers.

## ✨ Features

- **2GB Upload Support:** Bypasses the default 50MB limit using a local API server.
- **Async Queue Management:** Handles multiple downloads concurrently without blocking.
- **Chunked Processing:** Downloads and uploads in 1MB chunks to ensure low memory footprint.
- **Admin Only:** Restricts access to specific Telegram user IDs.
- **Progress Tracking:** Real-time updates on download progress, speed, and status.
- **Dockerized:** Easy deployment using Docker Compose.

---

## 📋 Prerequisites

Before you begin, you will need:

1.  **Telegram API Credentials:**
    -   Go to [my.telegram.org](https://my.telegram.org), log in, and create an application to get your `API_ID` and `API_HASH`.
2.  **Bot Token:**
    -   Create a new bot via [@BotFather](https://t.me/BotFather) to get your `BOT_TOKEN`.
3.  **Target Group ID:**
    -   The ID of the group where files will be uploaded. (See "How to find IDs" below).
4.  **Admin User IDs:**
    -   Your own Telegram User ID (and any others you want to authorize).

---

## 🛠️ Installation & Setup (Docker Recommended)

The easiest way to run this bot is using **Docker Compose**, as it automatically manages both the Bot and the Local Telegram Bot API Server.

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/tg-download-bot.git
cd tg-download-bot
```

### 2. Configure Environment Variables
Copy the example environment file and fill in your details:
```bash
cp .env.example .env
```
Edit `.env` with your preferred text editor:
```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=[12345678]  # Your Telegram User ID
TARGET_GROUP_ID=-1001234567890 # Your Target Group ID
TELEGRAM_API_ID=12345
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_API_URL=http://telegram-bot-api:8081
```

### 3. Run with Docker Compose
```bash
docker-compose up --build -d
```
This will start:
-   `telegram-bot-api`: The local server for large uploads.
-   `bot`: The Python application handling logic.

---

## 🧪 How to Test in Telegram

Once the bot is running, follow these steps to verify it:

### 1. Find Your IDs (If you don't have them)
-   **User ID:** Send any message to [@userinfobot](https://t.me/userinfobot) to get your personal ID. Add this to `ADMIN_IDS`.
-   **Group ID:** 
    1.  Add the bot to your target group.
    2.  Promote the bot to **Admin** (required for large uploads).
    3.  Send a message in the group and then check `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` OR use a bot like [@MissRose_bot](https://t.me/MissRose_bot) and type `/id` in the group.

### 2. Start the Transfer
1.  Open a private chat with your bot.
2.  Send a direct download link (e.g., `https://example.com/very-large-file.zip`).
3.  The bot will:
    -   Confirm the task is in the queue.
    -   Show a progress bar with speed and percentage.
    -   Notify when it starts uploading to the group.
    -   Send a final "Success" message once the file appears in the target group.

### 👥 Group Usage (New!)
You can now trigger downloads directly from groups by tagging the bot:
1.  Add the bot to your group.
2.  Tag the bot and paste the link: `@YourBotName https://example.com/file.zip`
3.  **Pro-Tip (The Space Trick):** If typing the bot's name triggers "Inline Mode" (showing an 'X' instead of a 'Send' button), simply **put a space before the `@`** (e.g., ` @YourBotName [link]`) or type any character first.

---

## ⚙️ Essential Bot Configuration (BotFather)

To ensure the bot works correctly in groups, verify these settings in [@BotFather](https://t.me/BotFather):

1.  **Allow Groups:** `Bot Settings` > `Allow Groups?` > **ENABLED**.
2.  **Privacy Mode:** `Bot Settings` > `Group Privacy` > **DISABLED**. (This allows the bot to see links in groups it is an admin of).
3.  **Admin Rights:** The bot **MUST** be an Administrator in your target group to upload files larger than 50MB.

---

## 🔧 Manual Development Setup

If you want to run the bot without Docker for development:

1.  **Run the Local API Server:** You still need the `aiogram/telegram-bot-api` binary or container running locally.
2.  **Setup Python Venv:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Or .\venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```
3.  **Run Bot:**
    ```bash
    python bot/main.py
    ```

---

## 📁 Project Structure

```text
.
├── bot/
│   ├── main.py        # Entry point & event loop
│   ├── config.py      # Env var validation (Pydantic)
│   ├── handlers.py    # URL detection & message handling
│   └── downloader.py  # Chunked download/upload & Queue Worker
├── Dockerfile         # Bot image definition
└── docker-compose.yml # Orchestrates bot + API server
```

---

## ⚠️ Important Notes

-   **File Cleanup:** The bot automatically deletes files from the local disk after a successful or failed upload to prevent storage exhaustion.
-   **Disk Space:** Ensure your VPS/Server has enough disk space to temporarily hold the 2GB file during the transfer process.
-   **Rate Limits:** Progress updates are throttled to every 5 seconds to avoid Telegram API Flood limits.

---

## 🛠️ Troubleshooting

### Connection to Local API Server
If the bot fails to start or says it cannot reach the API server, you can run the connectivity test inside the Docker container:
```bash
docker-compose exec bot python bot/test_connectivity.py
```
This script verifies if the `bot` service can communicate with the `telegram-bot-api` service at `http://telegram-bot-api:8081`.

---

## 📄 License
MIT License. See [LICENSE](LICENSE) for more details.
