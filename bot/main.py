import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.filters import Command
from bot.config import settings

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

    # Echo handler
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer("Hello! I am your Download Bot. Send me a link to start.")

    @dp.message()
    async def echo_all(message: types.Message):
        if message.from_user.id not in settings.ADMIN_IDS:
            logger.warning(f"Unauthorized access attempt by user {message.from_user.id}")
            return
        
        await message.answer(f"Echo: {message.text}")

    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
