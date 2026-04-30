import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.filters import Command
from bot.config import settings
from bot.handlers import router
from bot.downloader import worker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Setup custom API server for Local Bot API
    session = AiohttpSession(
        api=TelegramAPIServer.from_base(settings.TELEGRAM_API_URL)
    )
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN, session=session)
    dp = Dispatcher()

    # Initialize download queue and store in dispatcher workflow data
    queue = asyncio.Queue()
    dp["download_queue"] = queue

    # Include handlers
    dp.include_router(router)

    # Start worker tasks
    workers = [
        asyncio.create_task(worker(bot, queue))
        for _ in range(5)
    ]

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
