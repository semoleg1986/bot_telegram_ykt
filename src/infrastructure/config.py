from __future__ import annotations

import os
from dataclasses import dataclass

from src.domain import Policy


def _split_list(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _split_int_list(raw: str | None) -> tuple[int, ...]:
    if not raw:
        return ()
    values: list[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        values.append(int(item))
    return tuple(values)


@dataclass(frozen=True)
class Settings:
    token: str
    admin_chat_id: int | None
    admin_user_ids: tuple[int, ...]
    db_path: str
    required_channel: str | None
    required_channel_link: str | None
    required_chat: str | None
    outline_api_url: str | None
    outline_cert_sha256: str | None
    vpn_ttl_days: int
    vpn_max_active_keys: int
    keyword_list: tuple[str, ...]
    domain_blacklist: tuple[str, ...]
    domain_whitelist: tuple[str, ...]
    max_links: int
    repeat_window_sec: int
    repeat_threshold: int


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise ValueError("BOT_TOKEN is required")
    admin_chat_id_raw = os.getenv("ADMIN_CHAT_ID")
    admin_chat_id = int(admin_chat_id_raw) if admin_chat_id_raw else None
    return Settings(
        token=token,
        admin_chat_id=admin_chat_id,
        admin_user_ids=_split_int_list(os.getenv("ADMIN_USER_IDS")),
        db_path=os.getenv("DB_PATH", "data/bot.sqlite3"),
        required_channel=os.getenv("REQUIRED_CHANNEL"),
        required_channel_link=os.getenv("REQUIRED_CHANNEL_LINK"),
        required_chat=os.getenv("REQUIRED_CHAT"),
        outline_api_url=os.getenv("OUTLINE_API_URL"),
        outline_cert_sha256=os.getenv("OUTLINE_CERT_SHA256"),
        vpn_ttl_days=int(os.getenv("VPN_TTL_DAYS", "30")),
        vpn_max_active_keys=int(os.getenv("VPN_MAX_ACTIVE_KEYS", "2")),
        keyword_list=_split_list(os.getenv("SPAM_KEYWORDS")),
        domain_blacklist=_split_list(os.getenv("SPAM_DOMAINS")),
        domain_whitelist=_split_list(os.getenv("ALLOW_DOMAINS")),
        max_links=int(os.getenv("MAX_LINKS", "2")),
        repeat_window_sec=int(os.getenv("REPEAT_WINDOW_SEC", "300")),
        repeat_threshold=int(os.getenv("REPEAT_THRESHOLD", "2")),
    )


def build_policy(settings: Settings) -> Policy:
    return Policy(
        keyword_list=settings.keyword_list,
        domain_blacklist=settings.domain_blacklist,
        domain_whitelist=settings.domain_whitelist,
        max_links=settings.max_links,
        repeat_window_sec=settings.repeat_window_sec,
        repeat_threshold=settings.repeat_threshold,
    ).normalized()
