import asyncio
import logging
import re
from aiogram import Router, types, F, Bot
from aiogram.enums import ChatType
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router()

# Simple regex for URL detection
URL_PATTERN = re.compile(
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)


@router.message(F.text)
async def handle_message(message: types.Message, bot: Bot, download_queue: asyncio.Queue):
    is_private = message.chat.type == ChatType.PRIVATE
    
    # For non-private chats, we only respond if the bot is mentioned
    bot_info = await bot.get_me()
    is_mentioned = bot_info.username and f"@{bot_info.username}" in message.text

    if not is_private and not is_mentioned:
        return

    if message.from_user.id not in settings.ADMIN_IDS:
        logger.warning(f"Unauthorized access attempt by user {message.from_user.id}")
        if is_private or is_mentioned:
            await message.answer("❌ **Access Denied.**\nYou are not authorized to use this bot.")
        return

    urls = URL_PATTERN.findall(message.text)
    if not urls:
        if is_private or is_mentioned:
            await message.answer("Please send a valid download link.")
        return

    # Use the first URL found
    url = urls[0]

    status_msg = await message.answer(
        "⏳ **Task added to queue.**\nPlease wait for the download to start...",
        parse_mode="Markdown",
    )

    await download_queue.put((url, message.chat.id, status_msg.message_id))
