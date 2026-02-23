from __future__ import annotations

from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.application import PolicyStore, VpnIssuer

from ..utils import format_policy_summary, is_admin, is_channel_member, schedule_delete


def _build_menu() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Статистика", callback_data="menu:stats"),
            InlineKeyboardButton(text="VPN ключ", callback_data="menu:vpn"),
        ],
        [
            InlineKeyboardButton(
                text="Добавить слово", callback_data="menu:add_keyword"
            ),
            InlineKeyboardButton(
                text="Удалить слово", callback_data="menu:remove_keyword"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Добавить домен", callback_data="menu:add_domain"
            ),
            InlineKeyboardButton(
                text="Удалить домен", callback_data="menu:remove_domain"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def register_menu_handlers(
    router: Router,
    bot: Bot,
    policy_store: PolicyStore,
    vpn_issuer: VpnIssuer,
    admin_user_ids: set[int],
    required_channel: str | None = None,
    required_channel_link: str | None = None,
    required_chat: str | None = None,
) -> None:
    @router.message(Command("menu"))
    async def on_menu(message: types.Message) -> None:
        sent = await message.reply("Меню управления:", reply_markup=_build_menu())
        schedule_delete(bot, sent)

    @router.callback_query()
    async def on_menu_callback(query: types.CallbackQuery) -> None:
        data = query.data or ""
        if not data.startswith("menu:"):
            return

        await query.answer()
        if not query.message:
            return

        if data in {
            "menu:stats",
            "menu:add_keyword",
            "menu:remove_keyword",
            "menu:add_domain",
            "menu:remove_domain",
        }:
            if not query.from_user:
                return
            admin = await is_admin(
                bot, query.message.chat.id, query.from_user.id, admin_user_ids
            )
            if not admin:
                sent = await query.message.reply(
                    "Только администратор может выполнять это действие."
                )
                schedule_delete(bot, sent)
                return

        if data == "menu:stats":
            policy = await policy_store.get()
            sent = await query.message.reply(format_policy_summary(policy))
            schedule_delete(bot, sent)
            return

        if data == "menu:vpn":
            if not query.from_user:
                return
            admin = await is_admin(
                bot, query.message.chat.id, query.from_user.id, admin_user_ids
            )
            if required_chat and not admin:
                in_chat = await is_channel_member(
                    bot, required_chat, query.from_user.id
                )
                if not in_chat:
                    chat_link = f"https://t.me/{required_chat.lstrip('@')}"
                    sent = await query.message.reply(
                        "VPN доступ только для участников чата: " + chat_link
                    )
                    schedule_delete(bot, sent)
                    return
            if required_channel and not admin:
                member = await is_channel_member(
                    bot, required_channel, query.from_user.id
                )
                if not member:
                    link = (
                        required_channel_link
                        or f"https://t.me/{required_channel.lstrip('@')}"
                    )
                    sent = await query.message.reply(
                        "Для получения VPN подпишитесь на канал: " + link
                    )
                    schedule_delete(bot, sent)
                    return
            access_key = await vpn_issuer.issue(query.from_user.id)
            sent = await query.message.reply(f"Ваш Outline ключ: {access_key}")
            schedule_delete(bot, sent)
            return

        if data == "menu:add_keyword":
            sent = await query.message.reply("Команда: /spam_add keyword <слово>")
            schedule_delete(bot, sent)
            return

        if data == "menu:remove_keyword":
            sent = await query.message.reply("Команда: /spam_remove keyword <слово>")
            schedule_delete(bot, sent)
            return

        if data == "menu:add_domain":
            sent = await query.message.reply("Команда: /spam_add domain <домен>")
            schedule_delete(bot, sent)
            return

        if data == "menu:remove_domain":
            sent = await query.message.reply("Команда: /spam_remove domain <домен>")
            schedule_delete(bot, sent)
            return
