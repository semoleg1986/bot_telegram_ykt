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
    monkeypatch.setenv("REQUIRED_CHANNEL", "@myyakutsk_info")
    monkeypatch.setenv("REQUIRED_CHANNEL_LINK", "https://t.me/myyakutsk_info")
    monkeypatch.setenv("SBER_RATES_URL", "https://example.com/sber")
    monkeypatch.setenv("VTB_RATES_URL", "https://example.com/vtb")
    monkeypatch.setenv("AEB_RATES_URL", "https://example.com/aeb")
    monkeypatch.setenv("AOSNGS_URL", "https://example.com/aosngs")
    monkeypatch.setenv(
        "TUNEFT_URLS",
        "https://example.com/t1,https://example.com/t2",
    )
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
    assert settings.required_channel == "@myyakutsk_info"
    assert settings.required_channel_link == "https://t.me/myyakutsk_info"
    assert settings.sber_rates_url == "https://example.com/sber"
    assert settings.vtb_rates_url == "https://example.com/vtb"
    assert settings.aeb_rates_url == "https://example.com/aeb"
    assert settings.aosngs_url == "https://example.com/aosngs"
    assert settings.tuneft_urls == ("https://example.com/t1", "https://example.com/t2")
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
