import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Provide a clean environment for testing."""
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.delenv("ADMIN_IDS", raising=False)
    monkeypatch.delenv("TARGET_GROUP_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_API_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_API_HASH", raising=False)
