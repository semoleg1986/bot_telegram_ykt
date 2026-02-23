from __future__ import annotations

import asyncio
import re
from typing import Any, Iterable

from src.domain import Policy

_URL_RE = re.compile(r"https?://\\S+")


def extract_urls(text: str | None, entities: Iterable[Any] | None) -> list[str]:
    if not text:
        return []
    urls: list[str] = []
    if entities:
        for entity in entities:
            if entity.type == "url":
                urls.append(text[entity.offset : entity.offset + entity.length])
            elif entity.type == "text_link" and entity.url:
                urls.append(entity.url)
    if not urls:
        urls.extend(_URL_RE.findall(text))
    return urls


async def is_admin(
    bot: Any, chat_id: int, user_id: int, admin_user_ids: set[int]
) -> bool:
    if user_id in admin_user_ids:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    return member.status in {"administrator", "creator"}


async def is_channel_member(bot: Any, channel: str, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(channel, user_id)
    except Exception:
        return False
    return member.status in {"member", "administrator", "creator"}


def split_args(text: str) -> list[str]:
    if not text:
        return []
    return [part for part in text.strip().split() if part]


def format_policy_summary(policy: Policy) -> str:
    return (
        "Текущая политика:\n"
        f"- ключевые слова: {len(policy.keyword_list)}\n"
        f"- blacklist доменов: {len(policy.domain_blacklist)}\n"
        f"- whitelist доменов: {len(policy.domain_whitelist)}\n"
        f"- max_links: {policy.max_links}\n"
        f"- repeat_threshold: {policy.repeat_threshold}"
    )


def apply_policy_add(policy: Policy, kind: str, value: str) -> Policy:
    kind = kind.lower()
    value = value.lower()
    if kind == "keyword":
        if value in policy.keyword_list:
            return policy
        return Policy(
            keyword_list=policy.keyword_list + (value,),
            domain_blacklist=policy.domain_blacklist,
            domain_whitelist=policy.domain_whitelist,
            max_links=policy.max_links,
            repeat_window_sec=policy.repeat_window_sec,
            repeat_threshold=policy.repeat_threshold,
        ).normalized()
    if kind == "domain":
        if value in policy.domain_blacklist:
            return policy
        return Policy(
            keyword_list=policy.keyword_list,
            domain_blacklist=policy.domain_blacklist + (value,),
            domain_whitelist=policy.domain_whitelist,
            max_links=policy.max_links,
            repeat_window_sec=policy.repeat_window_sec,
            repeat_threshold=policy.repeat_threshold,
        ).normalized()
    return policy


def apply_policy_remove(policy: Policy, kind: str, value: str) -> Policy:
    kind = kind.lower()
    value = value.lower()
    if kind == "keyword":
        return Policy(
            keyword_list=tuple(k for k in policy.keyword_list if k != value),
            domain_blacklist=policy.domain_blacklist,
            domain_whitelist=policy.domain_whitelist,
            max_links=policy.max_links,
            repeat_window_sec=policy.repeat_window_sec,
            repeat_threshold=policy.repeat_threshold,
        ).normalized()
    if kind == "domain":
        return Policy(
            keyword_list=policy.keyword_list,
            domain_blacklist=tuple(d for d in policy.domain_blacklist if d != value),
            domain_whitelist=policy.domain_whitelist,
            max_links=policy.max_links,
            repeat_window_sec=policy.repeat_window_sec,
            repeat_threshold=policy.repeat_threshold,
        ).normalized()
    return policy


def schedule_delete(bot: Any, message: Any, delay: int = 10) -> None:
    if not message or not getattr(message, "chat", None):
        return
    chat_type = getattr(message.chat, "type", "")
    if chat_type not in {"group", "supergroup"}:
        return

    async def _delete() -> None:
        await asyncio.sleep(delay)
        try:
            await bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass

    asyncio.create_task(_delete())
