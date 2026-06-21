import json

from app.utils.texts import TextManager


def _make(tmp_path, data):
    p = tmp_path / "texts.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return TextManager(str(p))


def test_nested_lookup_and_formatting(tmp_path):
    tm = _make(tmp_path, {"user": {"hi": "Hello {name}"}})
    assert tm.get("user", "hi", name="Alice") == "Hello Alice"


def test_plain_lookup_without_kwargs(tmp_path):
    tm = _make(tmp_path, {"user": {"hi": "Hello {name}"}})
    # Без kwargs строка возвращается как есть, без .format()
    assert tm.get("user", "hi") == "Hello {name}"


def test_missing_key_returns_safe_placeholder(tmp_path):
    tm = _make(tmp_path, {"user": {}})
    assert tm.get("user", "nope") == "[user.nope]"


def test_missing_format_kwarg_returns_raw_string(tmp_path):
    tm = _make(tmp_path, {"user": {"hi": "Hello {name}"}})
    # Отсутствующий kwarg не должен ронять бот — возвращаем исходную строку
    assert tm.get("user", "hi", other="x") == "Hello {name}"


def test_helper_methods(tmp_path):
    tm = _make(tmp_path, {"buttons": {"back": "Назад"}, "errors": {"unknown": "Ошибка"}})
    assert tm.get_button_text("back") == "Назад"
    assert tm.get_error_text("unknown") == "Ошибка"
