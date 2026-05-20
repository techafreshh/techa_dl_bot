import asyncio
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.downloader import worker
from bot.config import settings

@pytest.mark.asyncio
async def test_worker_successful_flow(tmp_path):
    # Setup mocks
    bot = AsyncMock()
    queue = asyncio.Queue()
    
    # Mock settings.DOWNLOAD_DIR to use tmp_path
    with patch("bot.downloader.settings") as mock_settings:
        mock_settings.DOWNLOAD_DIR = str(tmp_path)
        mock_settings.TARGET_GROUP_ID = 123456789
        
        # Mock uuid to have predictable paths
        with patch("uuid.uuid4") as mock_uuid:
            mock_uuid.side_effect = [
                MagicMock(hex="temp_uuid"),
                MagicMock(hex="task_uuid")
            ]
            
            # Mock DownloadManager.download
            async def mock_download_side_effect(url, destination, progress_callback):
                # Create the dummy file that os.rename expects
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                with open(destination, "w") as f:
                    f.write("dummy data")
                return True, "test_file.zip"

            with patch("bot.downloader.DownloadManager.download", new_callable=AsyncMock) as mock_download:
                mock_download.side_effect = mock_download_side_effect
                
                # Put a task in the queue
                await queue.put(("http://example.com/file.zip", 111, 222))
                
                # Use a helper to stop the worker after one task
                async def stop_worker():
                    while not queue.empty():
                        await asyncio.sleep(0.1)
                    # Give it a bit more time to finish processing
                    await asyncio.sleep(0.5)
                    raise asyncio.CancelledError()

                # Run worker and stop it
                try:
                    await asyncio.gather(
                        worker(bot, queue),
                        stop_worker()
                    )
                except asyncio.CancelledError:
                    pass
                
                # Assertions
                mock_download.assert_called_once()
                
                # Check if send_document was called correctly
                bot.send_document.assert_called_once()
                call_args = bot.send_document.call_args[1]
                assert call_args["chat_id"] == 123456789
                from aiogram.types import FSInputFile
                assert isinstance(call_args["document"], FSInputFile)
                assert "test_file.zip" in call_args["document"].path
                assert "task_uuid" in call_args["document"].path
                assert call_args["caption"] == "test_file.zip"
                # Verify cleanup: task_dir should be gone
                dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
                assert len(dirs) == 0, f"Expected task_dir to be cleaned up, but found: {dirs}"

@pytest.mark.asyncio
async def test_worker_failed_download_cleanup(tmp_path):
    # Setup mocks
    bot = AsyncMock()
    queue = asyncio.Queue()
    
    with patch("bot.downloader.settings") as mock_settings:
        mock_settings.DOWNLOAD_DIR = str(tmp_path)
        
        with patch("bot.downloader.DownloadManager.download", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = (False, "")
            
            await queue.put(("http://example.com/fail.zip", 111, 222))
            
            async def stop_worker():
                while not queue.empty():
                    await asyncio.sleep(0.1)
                await asyncio.sleep(0.2)
                raise asyncio.CancelledError()

            try:
                await asyncio.gather(
                    worker(bot, queue),
                    stop_worker()
                )
            except asyncio.CancelledError:
                pass
            
            # Assertions
            bot.send_document.assert_not_called()
            
            # Verify cleanup
            remaining_files = list(tmp_path.iterdir())
            assert len(remaining_files) == 0
