from __future__ import annotations

from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.application import PolicyStore, VpnIssuer

from ..utils import format_policy_summary, is_admin


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
) -> None:
    @router.message(Command("menu"))
    async def on_menu(message: types.Message) -> None:
        await message.reply("Меню управления:", reply_markup=_build_menu())

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
                await query.message.reply(
                    "Только администратор может выполнять это действие."
                )
                return

        if data == "menu:stats":
            policy = await policy_store.get()
            await query.message.reply(format_policy_summary(policy))
            return

        if data == "menu:vpn":
            if not query.from_user:
                return
            access_key = await vpn_issuer.issue(query.from_user.id)
            await query.message.reply(f"Ваш Outline ключ: {access_key}")
            return

        if data == "menu:add_keyword":
            await query.message.reply("Команда: /spam_add keyword <слово>")
            return

        if data == "menu:remove_keyword":
            await query.message.reply("Команда: /spam_remove keyword <слово>")
            return

        if data == "menu:add_domain":
            await query.message.reply("Команда: /spam_add domain <домен>")
            return

        if data == "menu:remove_domain":
            await query.message.reply("Команда: /spam_remove domain <домен>")
            return
