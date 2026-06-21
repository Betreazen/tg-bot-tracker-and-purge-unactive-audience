import pytest

from app.utils.config import Config

REQUIRED = {
    "BOT_TOKEN": "123:ABC",
    "CHANNEL_ID": "-1001234567890",
    "CHANNEL_USERNAME": "my_channel",
    "ADMIN_IDS": "111, 222 ,333",
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
    "REDIS_URL": "redis://localhost:6379/0",
}


def _set_required(monkeypatch, overrides=None):
    # Отключаем чтение .env, чтобы тесты не зависели от окружения
    monkeypatch.setattr("app.utils.config.load_dotenv", lambda *a, **k: None)
    values = dict(REQUIRED)
    if overrides:
        values.update(overrides)
    for key in list(REQUIRED) + ["TIMEZONE", "LOG_PATH"]:
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_admin_ids_parsed_and_trimmed(monkeypatch):
    _set_required(monkeypatch)
    cfg = Config()
    assert cfg.ADMIN_IDS == [111, 222, 333]
    assert cfg.CHANNEL_ID == -1001234567890
    assert cfg.is_admin(222) is True
    assert cfg.is_admin(999) is False


def test_missing_required_raises(monkeypatch):
    _set_required(monkeypatch, overrides=None)
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(ValueError):
        Config()


def test_invalid_admin_ids_raises(monkeypatch):
    _set_required(monkeypatch, overrides={"ADMIN_IDS": "111,abc"})
    with pytest.raises(ValueError):
        Config()


def test_timezone_default(monkeypatch):
    _set_required(monkeypatch)
    cfg = Config()
    assert cfg.TIMEZONE == "Europe/Moscow"
