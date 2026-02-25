from __future__ import annotations

import asyncio

from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.application import PolicyStore, VpnIssuer
from src.infrastructure.clients.market_data import MarketDataService

from ..utils import format_policy_summary, is_admin, is_channel_member, schedule_delete
from .service import _format_fuel_table, _format_rates_table


def _build_main_menu() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="VPN", callback_data="menu:vpn_root"),
            InlineKeyboardButton(text="Спам", callback_data="menu:spam_root"),
        ],
        [
            InlineKeyboardButton(text="Сервис", callback_data="menu:service_root"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _build_vpn_menu(outline_enabled: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Получить Xray", callback_data="menu:vpn")],
        [
            InlineKeyboardButton(
                text="Отозвать мой ключ", callback_data="menu:vpn_revoke_self"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отозвать по ID", callback_data="menu:vpn_revoke_by_id"
            )
        ],
        [InlineKeyboardButton(text="Статистика", callback_data="menu:vpn_stats")],
        [InlineKeyboardButton(text="Пользователи", callback_data="menu:vpn_users")],
    ]
    if outline_enabled:
        rows.extend(
            [
                [
                    InlineKeyboardButton(
                        text="Получить Outline", callback_data="menu:outline"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Outline: отозвать мой",
                        callback_data="menu:outline_revoke_self",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Outline: отозвать по ID",
                        callback_data="menu:outline_revoke_by_id",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Outline: статистика", callback_data="menu:outline_stats"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Outline: пользователи", callback_data="menu:outline_users"
                    )
                ],
            ]
        )
    rows.append([InlineKeyboardButton(text="Назад", callback_data="menu:back")])
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
    vpn_issuer: VpnIssuer,
    outline_issuer: VpnIssuer | None,
    market: MarketDataService,
    admin_user_ids: set[int],
    required_channel: str | None = None,
    required_channel_link: str | None = None,
    required_chat: str | None = None,
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
            "menu:vpn_stats",
            "menu:vpn_users",
            "menu:vpn_revoke_by_id",
            "menu:outline_stats",
            "menu:outline_users",
            "menu:outline_revoke_by_id",
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

        if data == "menu:vpn_root":
            sent = await bot.send_message(
                chat_id,
                "VPN меню:",
                reply_markup=_build_vpn_menu(outline_issuer is not None),
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
                    sent = await bot.send_message(
                        chat_id, "VPN доступ только для участников чата: " + chat_link
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
                    sent = await bot.send_message(
                        chat_id, "Для получения VPN подпишитесь на канал: " + link
                    )
                    schedule_delete(bot, sent)
                    return
            access_key = await vpn_issuer.issue(query.from_user.id)
            sent = await bot.send_message(
                chat_id,
                "Ваш VLESS профиль (Xray):\n"
                "```\n"
                f"{access_key}\n"
                "```\n"
                "Инструкция:\n"
                "1) Установите V2Ray/Xray клиент\n"
                "2) Скопируйте ссылку из блока выше\n"
                "3) В клиенте выберите Import from clipboard\n"
                "4) Нажмите Connect",
                parse_mode="Markdown",
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:outline":
            if not outline_issuer:
                sent = await bot.send_message(chat_id, "Outline не настроен.")
                schedule_delete(bot, sent)
                return
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
                    sent = await bot.send_message(
                        chat_id, "VPN доступ только для участников чата: " + chat_link
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
                    sent = await bot.send_message(
                        chat_id, "Для получения VPN подпишитесь на канал: " + link
                    )
                    schedule_delete(bot, sent)
                    return
            access_key = await outline_issuer.issue(query.from_user.id)
            sent = await bot.send_message(
                chat_id,
                "Ваш Outline ключ:\n"
                f"{access_key}\n\n"
                "Инструкция:\n"
                "1) Установите Outline Client\n"
                "2) Импортируйте ключ\n"
                "3) Нажмите Connect",
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:vpn_revoke_self":
            if not query.from_user:
                return
            await vpn_issuer.revoke(query.from_user.id)
            sent = await bot.send_message(chat_id, "Ключ отозван.")
            schedule_delete(bot, sent)
            return

        if data == "menu:outline_revoke_self":
            if not outline_issuer:
                sent = await bot.send_message(chat_id, "Outline не настроен.")
                schedule_delete(bot, sent)
                return
            if not query.from_user:
                return
            await outline_issuer.revoke(query.from_user.id)
            sent = await bot.send_message(chat_id, "Ключ отозван.")
            schedule_delete(bot, sent)
            return

        if data == "menu:vpn_revoke_by_id":
            sent = await bot.send_message(
                chat_id, "Команда: /vpn_revoke <user_id> (только админ)"
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:outline_revoke_by_id":
            sent = await bot.send_message(
                chat_id, "Команда: /outline_revoke <user_id> (только админ)"
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:vpn_stats":
            stats = await vpn_issuer.stats()
            sent = await bot.send_message(
                chat_id,
                "VPN статистика (Xray):\n"
                f"- всего ключей: {stats['total']}\n"
                f"- активные: {stats['active']}\n"
                f"- отозванные: {stats['revoked']}",
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:outline_stats":
            if not outline_issuer:
                sent = await bot.send_message(chat_id, "Outline не настроен.")
                schedule_delete(bot, sent)
                return
            stats = await outline_issuer.stats()
            sent = await bot.send_message(
                chat_id,
                "VPN статистика (Outline):\n"
                f"- всего ключей: {stats['total']}\n"
                f"- активные: {stats['active']}\n"
                f"- отозванные: {stats['revoked']}",
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:vpn_users":
            users = await vpn_issuer.active_users(limit=200)
            if not users:
                sent = await bot.send_message(chat_id, "Активных пользователей нет.")
                schedule_delete(bot, sent)
                return
            sent = await bot.send_message(
                chat_id, "Активные пользователи:\n" + "\n".join(map(str, users))
            )
            schedule_delete(bot, sent)
            return

        if data == "menu:outline_users":
            if not outline_issuer:
                sent = await bot.send_message(chat_id, "Outline не настроен.")
                schedule_delete(bot, sent)
                return
            users = await outline_issuer.active_users(limit=200)
            if not users:
                sent = await bot.send_message(chat_id, "Активных пользователей нет.")
                schedule_delete(bot, sent)
                return
            sent = await bot.send_message(
                chat_id, "Активные пользователи:\n" + "\n".join(map(str, users))
            )
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
                "/vpn\n"
                "/vpn_revoke\n"
                "/vpn_revoke <user_id>\n"
                "/vpn_stats\n"
                "/vpn_users\n"
                "/outline\n"
                "/outline_revoke\n"
                "/outline_revoke <user_id>\n"
                "/outline_stats\n"
                "/outline_users\n"
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
