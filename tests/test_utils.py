import pytest
from bot.utils import get_filename_from_headers, get_extension_from_mime

def test_get_extension_from_mime():
    assert get_extension_from_mime("video/x-matroska") == ".mkv"
    assert get_extension_from_mime("application/pdf") == ".pdf"
    assert get_extension_from_mime("image/jpeg") == ".jpg"
    assert get_extension_from_mime("") is None
    assert get_extension_from_mime(None) is None

def test_get_filename_from_headers_content_disposition_filename():
    headers = {"Content-Disposition": 'attachment; filename="movie.mkv"'}
    url = "http://example.com/download"
    assert get_filename_from_headers(headers, url) == "movie.mkv"

def test_get_filename_from_headers_content_disposition_filename_star():
    headers = {"Content-Disposition": "attachment; filename*=UTF-8''my%20file.mp4"}
    url = "http://example.com/download"
    assert get_filename_from_headers(headers, url) == "my file.mp4"

def test_get_filename_from_headers_content_disposition_both():
    # filename* should have priority
    headers = {
        "Content-Disposition": 'attachment; filename="wrong.txt"; filename*=UTF-8\'\'correct.mp4'
    }
    url = "http://example.com/download"
    assert get_filename_from_headers(headers, url) == "correct.mp4"

def test_get_filename_from_headers_url_fallback():
    headers = {}
    url = "http://example.com/path/to/file.zip?query=1"
    assert get_filename_from_headers(headers, url) == "file.zip"

def test_get_filename_from_headers_mime_fallback():
    headers = {"Content-Type": "video/x-matroska"}
    url = "http://example.com/api/file/FnkWSika?download"
    assert get_filename_from_headers(headers, url) == "FnkWSika.mkv"

def test_get_filename_from_headers_unquote_url():
    headers = {}
    url = "http://example.com/Encoded%20File%20Name.txt"
    assert get_filename_from_headers(headers, url) == "Encoded File Name.txt"

def test_get_filename_from_headers_no_info():
    headers = {}
    url = "http://example.com/"
    assert get_filename_from_headers(headers, url) == "downloaded_file"

def test_get_filename_from_headers_mediafire_link():
    headers = {}
    url = "https://download1349.mediafire.com/ofgfwsu5x4lg7YDcZnRF53Dmr1ivcbsG_K8DDxP5O33y7CVv-P29ViTSFkwwOflI36P8NaXAx7X5BzLS6w-ua0LVJ52ixz8Iz5VXuK3p11Javw9rOfzBUbGaO3fSlDyALZz3fAOj4IDVHx1Z5YpUSzbuApqrLHgtjrR-ezmDPEHb_Q/88kvj2u8r4i14cc/The+Boys.2019.S02E01.mp4.mp4"
    # urlparse(url).path is /.../The+Boys.2019.S02E01.mp4.mp4
    # unquote transforms + to space and %xx to chars
    assert get_filename_from_headers(headers, url) == "The Boys.2019.S02E01.mp4.mp4"

def test_get_filename_from_headers_sanitization():
    headers = {"Content-Disposition": 'attachment; filename="unsafe/file\\name:with*special?chars.txt"'}
    url = "http://example.com/download"
    # / \ : * ? should be replaced by _
    assert get_filename_from_headers(headers, url) == "unsafe_file_name_with_special_chars.txt"

def test_get_filename_from_headers_long_filename():
    long_name = "a" * 300 + ".txt"
    headers = {"Content-Disposition": f'attachment; filename="{long_name}"'}
    url = "http://example.com/download"
    result = get_filename_from_headers(headers, url)
    assert len(result) == 255
    assert result.endswith("aaaaaaaaaa")
