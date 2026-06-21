from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from app.services.user_service import UserService
from app.database.models import User


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


def _make_session(existing_user):
    session = MagicMock()
    session.execute = AsyncMock(return_value=_Result(existing_user))
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


async def test_create_new_user_returns_created_true(monkeypatch):
    monkeypatch.setattr(
        UserService, "get_current_time", staticmethod(lambda: datetime(2020, 1, 1))
    )
    session = _make_session(existing_user=None)

    user, created = await UserService.create_or_update_user(
        session, user_id=1, username="u", first_name="f", last_name="l"
    )

    assert created is True
    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    assert user.user_id == 1


async def test_update_existing_user_returns_created_false(monkeypatch):
    monkeypatch.setattr(
        UserService, "get_current_time", staticmethod(lambda: datetime(2021, 5, 5))
    )
    existing = User(
        user_id=2,
        username="old",
        first_name="old",
        last_name="old",
        first_seen_at=datetime(2020, 1, 1),
        last_seen_at=datetime(2020, 1, 1),
    )
    session = _make_session(existing_user=existing)

    user, created = await UserService.create_or_update_user(
        session, user_id=2, username="new", first_name="new", last_name="new"
    )

    assert created is False
    session.add.assert_not_called()
    assert user.username == "new"
    assert user.last_seen_at == datetime(2021, 5, 5)


async def test_error_triggers_rollback(monkeypatch):
    monkeypatch.setattr(
        UserService, "get_current_time", staticmethod(lambda: datetime(2020, 1, 1))
    )
    session = _make_session(existing_user=None)
    session.commit = AsyncMock(side_effect=RuntimeError("boom"))

    try:
        await UserService.create_or_update_user(session, user_id=3)
    except RuntimeError:
        pass

    session.rollback.assert_awaited_once()
