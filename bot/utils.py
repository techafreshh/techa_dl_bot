import mimetypes
import os
import re
from typing import Optional
from urllib.parse import urlparse, unquote, unquote_plus


def get_extension_from_mime(mime_type: str) -> Optional[str]:
    """
    Guess the file extension based on the MIME type.
    """
    if not mime_type:
        return None
    
    # mimetypes.guess_extension returns .ext with the dot
    return mimetypes.guess_extension(mime_type.split(";")[0].strip())


def sanitize_filename(filename: str) -> str:
    """
    Remove or replace characters that are unsafe for filenames.
    """
    # Remove null bytes
    filename = filename.replace("\0", "")
    # Replace unsafe characters with underscores
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Trim to 255 characters (common filesystem limit)
    return filename[:255]


def get_filename_from_headers(headers: dict, url: str) -> str:
    """
    Extracts the filename from the Content-Disposition header if available,
    otherwise falls back to the URL path.
    """
    filename = None
    content_disp = headers.get("Content-Disposition", "")

    if content_disp:
        # RFC 6266: filename* has priority over filename
        # filename* format: UTF-8''encoded_name.ext
        star_match = re.search(r"filename\*=([^;]+)", content_disp, re.IGNORECASE)
        if star_match:
            star_val = star_match.group(1).strip()
            if "''" in star_val:
                try:
                    encoding, name = star_val.split("''", 1)
                    filename = unquote(name)
                except ValueError:
                    filename = unquote(star_val)
            else:
                filename = unquote(star_val)

        if not filename:
            # Traditional filename parameter
            name_match = re.search(r'filename="?([^";]+)"?', content_disp, re.IGNORECASE)
            if name_match:
                filename = name_match.group(1).strip()

    if not filename:
        # Fallback to URL path
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = "downloaded_file"
        else:
            # use unquote_plus to handle + as spaces in path
            filename = unquote_plus(filename)

    # If the filename doesn't have an extension, try guessing from Content-Type
    if "." not in filename:
        content_type = headers.get("Content-Type", "")
        ext = get_extension_from_mime(content_type)
        if ext:
            filename += ext

    return sanitize_filename(filename)
