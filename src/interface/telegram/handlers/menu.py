from __future__ import annotations

import asyncio

from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.application import PolicyStore
from src.infrastructure.clients.market_data import MarketDataService

from ..utils import format_policy_summary, is_admin, schedule_delete
from .service import _format_fuel_table, _format_rates_table


def _build_main_menu() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Спам", callback_data="menu:spam_root"),
            InlineKeyboardButton(text="Сервис", callback_data="menu:service_root"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _build_spam_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Статистика", callback_data="menu:stats")],
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
        [InlineKeyboardButton(text="Назад", callback_data="menu:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _build_service_menu() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Курсы валют", callback_data="menu:rates"),
            InlineKeyboardButton(text="Топливо", callback_data="menu:fuel"),
        ],
        [InlineKeyboardButton(text="Help", callback_data="menu:help")],
        [InlineKeyboardButton(text="Who am I", callback_data="menu:whoami")],
        [InlineKeyboardButton(text="Назад", callback_data="menu:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def register_menu_handlers(
    router: Router,
    bot: Bot,
    policy_store: PolicyStore,
    market: MarketDataService,
    admin_user_ids: set[int],
) -> None:
    @router.message(Command("menu"))
    async def on_menu(message: types.Message) -> None:
        sent = await bot.send_message(
            message.chat.id,
            "Меню управления:",
            reply_markup=_build_main_menu(),
        )
        schedule_delete(bot, sent)

    @router.callback_query()
    async def on_menu_callback(query: types.CallbackQuery) -> None:
        data = query.data or ""
        if not data.startswith("menu:"):
            return

        await query.answer()
        if not query.message:
            return
        chat_id = query.message.chat.id

        if data in {
            "menu:stats",
            "menu:add_keyword",
            "menu:remove_keyword",
            "menu:add_domain",
            "menu:remove_domain",
            "menu:rates",
            "menu:fuel",
        }:
            if not query.from_user:
                return
            admin = await is_admin(
                bot, query.message.chat.id, query.from_user.id, admin_user_ids
            )
            if not admin:
                sent = await bot.send_message(
                    chat_id, "Только администратор может выполнять это действие."
                )
                schedule_delete(bot, sent)
                return

        if data == "menu:spam_root":
            sent = await bot.send_message(
                chat_id, "Спам меню:", reply_markup=_build_spam_menu()
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:service_root":
            sent = await bot.send_message(
                chat_id, "Сервис меню:", reply_markup=_build_service_menu()
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:back":
            sent = await bot.send_message(
                chat_id, "Меню управления:", reply_markup=_build_main_menu()
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:stats":
            policy = await policy_store.get()
            sent = await bot.send_message(chat_id, format_policy_summary(policy))
            schedule_delete(bot, sent)
            return

        if data == "menu:rates":
            data_rates = await asyncio.to_thread(market.get_rates)
            sent = await bot.send_message(
                chat_id, _format_rates_table(data_rates), parse_mode="Markdown"
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:fuel":
            data_fuel = await asyncio.to_thread(market.get_fuel)
            sent = await bot.send_message(
                chat_id, _format_fuel_table(data_fuel), parse_mode="Markdown"
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:help":
            sent = await bot.send_message(
                chat_id,
                "Команды:\n"
                "/menu — меню с кнопками\n"
                "/spam_add keyword <слово>\n"
                "/spam_add domain <домен>\n"
                "/spam_remove keyword <слово>\n"
                "/spam_remove domain <домен>\n"
                "/spam_stats\n"
                "/rates\n"
                "/fuel\n"
                "/whoami\n"
                "/help",
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:whoami":
            if not query.from_user:
                return
            admin = await is_admin(
                bot, query.message.chat.id, query.from_user.id, admin_user_ids
            )
            sent = await bot.send_message(
                chat_id,
                (
                    f"user_id={query.from_user.id}, "
                    f"chat_id={query.message.chat.id}, admin={admin}"
                ),
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:add_keyword":
            sent = await bot.send_message(chat_id, "Команда: /spam_add keyword <слово>")
            schedule_delete(bot, sent)
            return

        if data == "menu:remove_keyword":
            sent = await bot.send_message(
                chat_id, "Команда: /spam_remove keyword <слово>"
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:add_domain":
            sent = await bot.send_message(chat_id, "Команда: /spam_add domain <домен>")
            schedule_delete(bot, sent)
            return

        if data == "menu:remove_domain":
            sent = await bot.send_message(
                chat_id, "Команда: /spam_remove domain <домен>"
            )
            schedule_delete(bot, sent)
            return
