from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.middlewares.throttling_middleware import ThrottlingMiddleware


def _event(user_id=5):
    return SimpleNamespace(from_user=SimpleNamespace(id=user_id))


async def test_allows_under_limit(monkeypatch):
    mw = ThrottlingMiddleware(limit=3, window=10)
    fake_redis = SimpleNamespace(register_event=AsyncMock(return_value=1))
    monkeypatch.setattr(
        "app.middlewares.throttling_middleware.get_redis", lambda: fake_redis
    )
    handler = AsyncMock(return_value="ok")

    result = await mw(handler, _event(), {})

    handler.assert_awaited_once()
    assert result == "ok"


async def test_drops_over_limit(monkeypatch):
    mw = ThrottlingMiddleware(limit=3, window=10)
    # count = limit + 2 -> сразу отбрасываем без предупреждения
    fake_redis = SimpleNamespace(register_event=AsyncMock(return_value=5))
    monkeypatch.setattr(
        "app.middlewares.throttling_middleware.get_redis", lambda: fake_redis
    )
    handler = AsyncMock()

    result = await mw(handler, _event(), {})

    handler.assert_not_awaited()
    assert result is None


async def test_fail_open_when_redis_unavailable(monkeypatch):
    mw = ThrottlingMiddleware(limit=3, window=10)

    def _raise():
        raise RuntimeError("redis not ready")

    monkeypatch.setattr(
        "app.middlewares.throttling_middleware.get_redis", _raise
    )
    handler = AsyncMock(return_value="passed")

    result = await mw(handler, _event(), {})

    # Redis недоступен — троттлинг не должен блокировать пользователя
    handler.assert_awaited_once()
    assert result == "passed"


async def test_no_user_passes_through(monkeypatch):
    mw = ThrottlingMiddleware(limit=1, window=10)
    handler = AsyncMock(return_value="x")
    event = SimpleNamespace(from_user=None)

    result = await mw(handler, event, {})

    handler.assert_awaited_once()
    assert result == "x"
