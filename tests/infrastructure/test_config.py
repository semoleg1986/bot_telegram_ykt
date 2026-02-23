import pytest

from src.infrastructure.config import build_policy, load_settings


def test_load_settings_requires_token(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(ValueError):
        load_settings()


def test_load_settings_parses_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("ADMIN_CHAT_ID", "123")
    monkeypatch.setenv("ADMIN_USER_IDS", "1,2,3")
    monkeypatch.setenv("DB_PATH", "data/test.sqlite3")
    monkeypatch.setenv("SPAM_KEYWORDS", "one, two")
    monkeypatch.setenv("SPAM_DOMAINS", "bad.example")
    monkeypatch.setenv("ALLOW_DOMAINS", "good.example")
    monkeypatch.setenv("MAX_LINKS", "5")
    monkeypatch.setenv("REPEAT_WINDOW_SEC", "100")
    monkeypatch.setenv("REPEAT_THRESHOLD", "3")

    settings = load_settings()
    assert settings.token == "token"
    assert settings.admin_chat_id == 123
    assert settings.admin_user_ids == (1, 2, 3)
    assert settings.db_path == "data/test.sqlite3"
    assert settings.keyword_list == ("one", "two")
    assert settings.domain_blacklist == ("bad.example",)
    assert settings.domain_whitelist == ("good.example",)
    assert settings.max_links == 5
    assert settings.repeat_window_sec == 100
    assert settings.repeat_threshold == 3


def test_build_policy_normalizes():
    settings = type(
        "S",
        (),
        {
            "keyword_list": ("One",),
            "domain_blacklist": ("Bad.Example",),
            "domain_whitelist": ("Good.Example",),
            "max_links": 2,
            "repeat_window_sec": 300,
            "repeat_threshold": 2,
        },
    )()
    policy = build_policy(settings)
    assert policy.keyword_list == ("one",)
    assert policy.domain_blacklist == ("bad.example",)
    assert policy.domain_whitelist == ("good.example",)
