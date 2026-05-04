import asyncio
import logging
import os
import time
import uuid
from typing import Callable, Optional, Any, Tuple

import aiohttp
import aiofiles
from aiogram import Bot
from bot.config import settings
from bot.utils import get_filename_from_headers

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
    ) -> Tuple[bool, str]:
        """
        Downloads a file from url to destination in chunks.
        progress_callback: (downloaded_bytes, total_bytes, speed_bps)
        Returns: (success, detected_filename)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=None) as response:
                    if response.status != 200:
                        logger.error(
                            f"Failed to download {url}, status: {response.status}"
                        )
                        return False, ""

                    detected_filename = get_filename_from_headers(response.headers, url)
                    total_size = int(response.headers.get("Content-Length", 0))
                    downloaded_size = 0
                    start_time = time.time()
                    last_update_time = start_time

                    os.makedirs(os.path.dirname(destination), exist_ok=True)

                    async with aiofiles.open(destination, "wb") as f:
                        async for chunk in response.content.iter_chunked(
                            self.chunk_size
                        ):
                            await f.write(chunk)
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

                    return True, detected_filename
        except Exception as e:
            logger.exception(f"Error during download of {url}: {e}")
            if os.path.exists(destination):
                os.remove(destination)
            return False, ""


async def worker(bot: Bot, queue: asyncio.Queue):
    """
    Worker task to process downloads from the queue.
    Task format: (url, chat_id, message_id)
    """
    dm = DownloadManager()
    while True:
        url, chat_id, status_msg_id = await queue.get()
        logger.info(f"Worker processing {url} for chat {chat_id}")

        # Use a unique name for the temporary file to avoid collisions
        temp_filename = f"dl_{uuid.uuid4().hex}"
        destination = os.path.join(settings.DOWNLOAD_DIR, temp_filename)

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
                    text=text,
                    chat_id=chat_id,
                    message_id=status_msg_id,
                    parse_mode="Markdown",
                )
            except Exception:
                pass  # Avoid spamming logs if message wasn't edited

        try:
            success, original_filename = await dm.download(
                url, destination, progress_callback
            )

            if success:
                # Ensure the file is readable by the local API server (different user/container)
                try:
                    os.chmod(destination, 0o666)
                except Exception as e:
                    logger.warning(f"Failed to set permissions on {destination}: {e}")

                await bot.edit_message_text(
                    text=f"📤 **Uploading {original_filename}...**",
                    chat_id=chat_id,
                    message_id=status_msg_id,
                    parse_mode="Markdown",
                )

                # Rename the file to its original sanitized name to help the API server
                # We keep the UUID prefix to avoid collisions in the shared directory
                final_filename = f"{uuid.uuid4().hex}_{original_filename}"
                final_destination = os.path.join(settings.DOWNLOAD_DIR, final_filename)
                os.rename(destination, final_destination)
                destination = final_destination # Update for finally block cleanup

                logger.info(f"Sending file via local path: {final_destination}")
                
                # Using a string with file:// prefix is the most reliable way 
                # to trigger local mode upload in the Bot API server.
                await bot.send_document(
                    chat_id=settings.TARGET_GROUP_ID,
                    document=f"file://{final_destination}",
                    caption=f"{original_filename}",
                )
                
                await bot.edit_message_text(
                    text=f"✅ **Successfully transferred:** {original_filename}",
                    chat_id=chat_id,
                    message_id=status_msg_id,
                    parse_mode="Markdown",
                )
            else:
                await bot.edit_message_text(
                    text="❌ **Failed to download the file.**",
                    chat_id=chat_id,
                    message_id=status_msg_id,
                    parse_mode="Markdown",
                )
        except Exception as e:
            logger.exception(f"Worker error: {e}")
            try:
                await bot.edit_message_text(
                    text=f"❌ **Error:** {str(e)}",
                    chat_id=chat_id,
                    message_id=status_msg_id,
                )
            except Exception:
                pass
        finally:
            if os.path.exists(destination):
                os.remove(destination)
            queue.task_done()
