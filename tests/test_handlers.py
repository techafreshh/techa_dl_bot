import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.enums import ChatType
from bot.handlers import handle_message
from bot.config import settings

@pytest.mark.asyncio
async def test_handle_message_private_success():
    # Setup
    message = AsyncMock()
    message.chat.type = ChatType.PRIVATE
    message.text = "https://example.com/file.zip"
    message.from_user.id = settings.ADMIN_IDS[0]
    
    bot = AsyncMock()
    bot.get_me.return_value = MagicMock(username="test_bot")
    
    queue = AsyncMock()
    
    # Execute
    await handle_message(message, bot, queue)
    
    # Assert
    message.answer.assert_called_once()
    assert "Task added to queue" in message.answer.call_args[0][0]
    queue.put.assert_called_once()

@pytest.mark.asyncio
async def test_handle_message_group_no_mention():
    # Setup
    message = AsyncMock()
    message.chat.type = ChatType.GROUP
    message.text = "https://example.com/file.zip"
    message.from_user.id = settings.ADMIN_IDS[0]
    
    bot = AsyncMock()
    bot.get_me.return_value = MagicMock(username="test_bot")
    
    queue = AsyncMock()
    
    # Execute
    await handle_message(message, bot, queue)
    
    # Assert - should return early without doing anything
    message.answer.assert_not_called()
    queue.put.assert_not_called()

@pytest.mark.asyncio
async def test_handle_message_group_with_mention_success():
    # Setup
    message = AsyncMock()
    message.chat.type = ChatType.GROUP
    message.text = "@test_bot https://example.com/file.zip"
    message.from_user.id = settings.ADMIN_IDS[0]
    
    bot = AsyncMock()
    bot.get_me.return_value = MagicMock(username="test_bot")
    
    queue = AsyncMock()
    
    # Execute
    await handle_message(message, bot, queue)
    
    # Assert
    message.answer.assert_called_once()
    assert "Task added to queue" in message.answer.call_args[0][0]
    queue.put.assert_called_once()

@pytest.mark.asyncio
async def test_handle_message_unauthorized():
    # Setup
    message = AsyncMock()
    message.chat.type = ChatType.PRIVATE
    message.text = "https://example.com/file.zip"
    message.from_user.id = 999999  # Non-admin ID
    
    bot = AsyncMock()
    bot.get_me.return_value = MagicMock(username="test_bot")
    
    queue = AsyncMock()
    
    # Execute
    await handle_message(message, bot, queue)
    
    # Assert
    message.answer.assert_called_once()
    assert "Access Denied" in message.answer.call_args[0][0]
    queue.put.assert_not_called()
