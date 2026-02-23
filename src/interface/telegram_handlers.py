from __future__ import annotations

import re
from typing import Iterable

from aiogram import Bot, Router, types
from aiogram.filters import Command

from src.application import PolicyStore, ProcessMessage, VpnIssuer
from src.domain import Message, Policy, User

_URL_RE = re.compile(r"https?://\\S+")


def _extract_urls(
    text: str | None, entities: Iterable[types.MessageEntity] | None
) -> list[str]:
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


async def _is_admin(
    bot: Bot, chat_id: int, user_id: int, admin_user_ids: set[int]
) -> bool:
    if user_id in admin_user_ids:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    return member.status in {"administrator", "creator"}


def _split_args(text: str) -> list[str]:
    if not text:
        return []
    return [part for part in text.strip().split() if part]


def _format_policy_summary(policy: Policy) -> str:
    return (
        "Текущая политика:\\n"
        f"- ключевые слова: {len(policy.keyword_list)}\\n"
        f"- blacklist доменов: {len(policy.domain_blacklist)}\\n"
        f"- whitelist доменов: {len(policy.domain_whitelist)}\\n"
        f"- max_links: {policy.max_links}\\n"
        f"- repeat_threshold: {policy.repeat_threshold}"
    )


def build_router(
    use_case: ProcessMessage,
    bot: Bot,
    context_provider,
    policy_store: PolicyStore,
    vpn_issuer: VpnIssuer,
    admin_user_ids: set[int],
) -> Router:
    router = Router()

    @router.message(Command("spam_stats"))
    async def on_spam_stats(message: types.Message) -> None:
        if not message.from_user:
            return
        if not await _is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        ):
            await message.reply("Только администратор может смотреть статистику.")
            return
        policy = await policy_store.get()
        await message.reply(_format_policy_summary(policy))

    @router.message(Command("spam_add"))
    async def on_spam_add(message: types.Message) -> None:
        if not message.from_user:
            return
        if not await _is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        ):
            await message.reply("Только администратор может менять правила.")
            return
        args = _split_args(message.text or "")
        if len(args) < 3:
            await message.reply(
                "Использование: /spam_add keyword <слово> | /spam_add domain <домен>"
            )
            return
        kind = args[1].lower()
        value = args[2].lower()

        def updater(policy):
            if kind == "keyword":
                if value not in policy.keyword_list:
                    return Policy(
                        keyword_list=policy.keyword_list + (value,),
                        domain_blacklist=policy.domain_blacklist,
                        domain_whitelist=policy.domain_whitelist,
                        max_links=policy.max_links,
                        repeat_window_sec=policy.repeat_window_sec,
                        repeat_threshold=policy.repeat_threshold,
                    ).normalized()
            elif kind == "domain":
                if value not in policy.domain_blacklist:
                    return Policy(
                        keyword_list=policy.keyword_list,
                        domain_blacklist=policy.domain_blacklist + (value,),
                        domain_whitelist=policy.domain_whitelist,
                        max_links=policy.max_links,
                        repeat_window_sec=policy.repeat_window_sec,
                        repeat_threshold=policy.repeat_threshold,
                    ).normalized()
            return policy

        updated = await policy_store.update(updater)
        await message.reply("Обновлено. " + _format_policy_summary(updated))

    @router.message(Command("spam_remove"))
    async def on_spam_remove(message: types.Message) -> None:
        if not message.from_user:
            return
        if not await _is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        ):
            await message.reply("Только администратор может менять правила.")
            return
        args = _split_args(message.text or "")
        if len(args) < 3:
            await message.reply(
                "Использование: /spam_remove keyword <слово> | "
                "/spam_remove domain <домен>"
            )
            return
        kind = args[1].lower()
        value = args[2].lower()

        def updater(policy):
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
                    domain_blacklist=tuple(
                        d for d in policy.domain_blacklist if d != value
                    ),
                    domain_whitelist=policy.domain_whitelist,
                    max_links=policy.max_links,
                    repeat_window_sec=policy.repeat_window_sec,
                    repeat_threshold=policy.repeat_threshold,
                ).normalized()
            return policy

        updated = await policy_store.update(updater)
        await message.reply("Обновлено. " + _format_policy_summary(updated))

    @router.message(Command("vpn"))
    async def on_vpn(message: types.Message) -> None:
        if not message.from_user:
            return
        access_key = await vpn_issuer.issue(message.from_user.id)
        await message.reply(f"Ваш Outline ключ: {access_key}")

    @router.message(Command("whoami"))
    async def on_whoami(message: types.Message) -> None:
        if not message.from_user:
            return
        is_admin = await _is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        )
        await message.reply(
            (
                f"user_id={message.from_user.id}, "
                f"chat_id={message.chat.id}, admin={is_admin}"
            )
        )

    @router.message()
    async def on_message(message: types.Message) -> None:
        if not message.from_user:
            return
        text = message.text or message.caption or ""
        urls = _extract_urls(message.text, message.entities)
        urls += _extract_urls(message.caption, message.caption_entities)

        domain_message = Message.from_text(
            message_id=message.message_id,
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            text=text,
        ).with_urls(urls)

        if text:
            context_provider.add_text(message.chat.id, message.from_user.id, text)

        is_admin = await _is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        )
        user = User(user_id=message.from_user.id, is_admin=is_admin)

        await use_case.execute(domain_message, user)

    return router
