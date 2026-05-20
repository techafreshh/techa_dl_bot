import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from bot.config import settings
from bot.handlers import router
from bot.downloader import worker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # Ensure download directory exists and is accessible
    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    try:
        os.chmod(settings.DOWNLOAD_DIR, 0o777)
    except Exception as e:
        logger.warning(f"Could not set permissions on {settings.DOWNLOAD_DIR}: {e}")

    # Setup custom API server for Local Bot API
    # is_local=True tells aiogram to pass the local file path to the API server
    # instead of uploading bytes via multipart. This works because both containers
    # share the same volume at /var/lib/telegram-bot-api.
    session = AiohttpSession(api=TelegramAPIServer.from_base(settings.TELEGRAM_API_URL, is_local=True))

    # Initialize bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN, session=session)
    dp = Dispatcher()

    # Initialize download queue and store in dispatcher workflow data
    queue = asyncio.Queue()
    dp["download_queue"] = queue

    # Include handlers
    dp.include_router(router)

    # Start worker tasks
    workers = [asyncio.create_task(worker(bot, queue)) for _ in range(5)]

    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        # Cancel workers on stop
        for w in workers:
            w.cancel()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
