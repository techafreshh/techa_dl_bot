import pytest
from pydantic import ValidationError
from bot.config import Settings


def test_settings_success(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123:abc")
    monkeypatch.setenv(
        "ADMIN_IDS", "[123, 456]"
    )  # Pydantic parses list from JSON array string or comma separated? We'll test JSON first. Wait, pydantic parsing for list depends on the implementation.
    monkeypatch.setenv("TARGET_GROUP_ID", "-100123")
    monkeypatch.setenv("TELEGRAM_API_ID", "111")
    monkeypatch.setenv("TELEGRAM_API_HASH", "hash123")

    # We bypass the .env file loading by passing _env_file=None
    settings = Settings(_env_file=None)
    assert settings.BOT_TOKEN == "123:abc"
    assert settings.TARGET_GROUP_ID == -100123
    assert settings.TELEGRAM_API_ID == 111
    assert settings.TELEGRAM_API_HASH == "hash123"


def test_settings_missing_required(monkeypatch):
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
