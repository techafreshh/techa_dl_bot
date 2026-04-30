import pytest
from unittest.mock import patch
from aioresponses import aioresponses
import aiohttp
from bot.downloader import DownloadManager


@pytest.mark.asyncio
async def test_successful_download(tmp_path):
    dm = DownloadManager(chunk_size=10)
    dest = tmp_path / "test_file.txt"
    url = "http://test.com/file.txt"

    with aioresponses() as m:
        m.get(url, status=200, body=b"test data content")
        success, filename = await dm.download(url, str(dest))

        assert success is True
        assert filename == "file.txt"
        assert dest.exists()
        assert dest.read_bytes() == b"test data content"


@pytest.mark.asyncio
async def test_failed_download_404(tmp_path):
    dm = DownloadManager()
    dest = tmp_path / "test_file_404.txt"
    url = "http://test.com/404"

    with aioresponses() as m:
        m.get(url, status=404)
        success, filename = await dm.download(url, str(dest))

        assert success is False
        assert filename == ""
        assert not dest.exists()


@pytest.mark.asyncio
async def test_exception_cleanup(tmp_path):
    dm = DownloadManager()
    dest = tmp_path / "test_file_exc.txt"
    url = "http://test.com/error"

    with aioresponses() as m:
        m.get(url, exception=aiohttp.ClientError("Mocked network error"))

        # Pre-create the destination file to simulate partial download cleanup
        dest.write_text("partial data")

        with patch("os.remove") as mock_remove:
            success, filename = await dm.download(url, str(dest))

            assert success is False
            assert filename == ""
            mock_remove.assert_called_once_with(str(dest))
