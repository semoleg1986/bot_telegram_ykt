from __future__ import annotations

from aiogram import Bot, Router, types
from aiogram.filters import Command

from src.application import PolicyStore

from ..utils import (
    apply_policy_add,
    apply_policy_remove,
    format_policy_summary,
    is_admin,
    schedule_delete,
    split_args,
)


def register_spam_handlers(
    router: Router,
    bot: Bot,
    policy_store: PolicyStore,
    admin_user_ids: set[int],
) -> None:
    @router.message(Command("spam_stats"))
    async def on_spam_stats(message: types.Message) -> None:
        if not message.from_user:
            return
        if not await is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        ):
            sent = await message.reply(
                "Только администратор может смотреть статистику."
            )
            schedule_delete(bot, sent)
            return
        policy = await policy_store.get()
        sent = await message.reply(format_policy_summary(policy))
        schedule_delete(bot, sent)

    @router.message(Command("spam_add"))
    async def on_spam_add(message: types.Message) -> None:
        if not message.from_user:
            return
        if not await is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        ):
            sent = await message.reply("Только администратор может менять правила.")
            schedule_delete(bot, sent)
            return
        args = split_args(message.text or "")
        if len(args) < 3:
            sent = await message.reply(
                "Использование: /spam_add keyword <слово> | /spam_add domain <домен>"
            )
            schedule_delete(bot, sent)
            return
        kind = args[1]
        value = args[2]

        def updater(policy):
            return apply_policy_add(policy, kind, value)

        updated = await policy_store.update(updater)
        sent = await message.reply("Обновлено. " + format_policy_summary(updated))
        schedule_delete(bot, sent)

    @router.message(Command("spam_remove"))
    async def on_spam_remove(message: types.Message) -> None:
        if not message.from_user:
            return
        if not await is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        ):
            sent = await message.reply("Только администратор может менять правила.")
            schedule_delete(bot, sent)
            return
        args = split_args(message.text or "")
        if len(args) < 3:
            sent = await message.reply(
                "Использование: /spam_remove keyword <слово> | "
                "/spam_remove domain <домен>"
            )
            schedule_delete(bot, sent)
            return
        kind = args[1]
        value = args[2]

        def updater(policy):
            return apply_policy_remove(policy, kind, value)

        updated = await policy_store.update(updater)
        sent = await message.reply("Обновлено. " + format_policy_summary(updated))
        schedule_delete(bot, sent)
