import asyncio
import logging
import os
import time
from typing import Callable, Optional, Any
from urllib.parse import urlparse

import aiohttp
from aiogram import Bot
from aiogram.types import FSInputFile
from bot.config import settings

logger = logging.getLogger(__name__)


def format_size(bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} PB"


class DownloadManager:
    def __init__(self, chunk_size: int = 1024 * 1024):  # 1MB chunks
        self.chunk_size = chunk_size

    async def download(
        self,
        url: str,
        destination: str,
        progress_callback: Optional[Callable[[int, int, float], Any]] = None,
    ) -> bool:
        """
        Downloads a file from url to destination in chunks.
        progress_callback: (downloaded_bytes, total_bytes, speed_bps)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=None) as response:
                    if response.status != 200:
                        logger.error(
                            f"Failed to download {url}, status: {response.status}"
                        )
                        return False

                    total_size = int(response.headers.get("Content-Length", 0))
                    downloaded_size = 0
                    start_time = time.time()
                    last_update_time = start_time

                    os.makedirs(os.path.dirname(destination), exist_ok=True)

                    with open(destination, "wb") as f:
                        async for chunk in response.content.iter_chunked(
                            self.chunk_size
                        ):
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            current_time = time.time()
                            # Update progress every 5 seconds or if finished
                            if progress_callback and (
                                current_time - last_update_time > 5
                                or downloaded_size == total_size
                            ):
                                elapsed_time = current_time - start_time
                                speed = (
                                    downloaded_size / elapsed_time
                                    if elapsed_time > 0
                                    else 0
                                )
                                if asyncio.iscoroutinefunction(progress_callback):
                                    await progress_callback(
                                        downloaded_size, total_size, speed
                                    )
                                else:
                                    progress_callback(
                                        downloaded_size, total_size, speed
                                    )
                                last_update_time = current_time

                    return True
        except Exception as e:
            logger.exception(f"Error during download of {url}: {e}")
            if os.path.exists(destination):
                os.remove(destination)
            return False


async def worker(bot: Bot, queue: asyncio.Queue):
    """
    Worker task to process downloads from the queue.
    Task format: (url, chat_id, message_id)
    """
    dm = DownloadManager()
    while True:
        url, chat_id, status_msg_id = await queue.get()
        logger.info(f"Worker processing {url} for chat {chat_id}")

        filename = os.path.basename(urlparse(url).path) or "downloaded_file"
        destination = os.path.join(
            settings.DOWNLOAD_DIR, f"{int(time.time())}_{filename}"
        )

        async def progress_callback(downloaded, total, speed):
            percent = (downloaded / total * 100) if total > 0 else 0
            text = (
                f"📥 **Downloading...**\n"
                f"Progress: {format_size(downloaded)} / {format_size(total) if total > 0 else 'Unknown'}\n"
                f"Percentage: {percent:.2f}%\n"
                f"Speed: {format_size(int(speed))}/s"
            )
            try:
                await bot.edit_message_text(
                    text, chat_id, status_msg_id, parse_mode="Markdown"
                )
            except Exception:
                pass  # Avoid spamming logs if message wasn't edited

        try:
            success = await dm.download(url, destination, progress_callback)

            if success:
                await bot.edit_message_text(
                    "📤 **Uploading to Telegram...**",
                    chat_id,
                    status_msg_id,
                    parse_mode="Markdown",
                )
                document = FSInputFile(destination)
                await bot.send_document(
                    chat_id=settings.TARGET_GROUP_ID,
                    document=document,
                    caption=f"File: {filename}\nSource: {url}",
                )
                await bot.edit_message_text(
                    "✅ **Successfully transferred!**",
                    chat_id,
                    status_msg_id,
                    parse_mode="Markdown",
                )
            else:
                await bot.edit_message_text(
                    "❌ **Failed to download the file.**",
                    chat_id,
                    status_msg_id,
                    parse_mode="Markdown",
                )
        except Exception as e:
            logger.exception(f"Worker error: {e}")
            try:
                await bot.edit_message_text(
                    f"❌ **Error:** {str(e)}", chat_id, status_msg_id
                )
            except Exception:
                pass
        finally:
            if os.path.exists(destination):
                os.remove(destination)
            queue.task_done()
