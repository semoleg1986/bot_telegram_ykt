from __future__ import annotations

from aiogram import Bot, Router, types
from aiogram.filters import Command

from src.application import VpnIssuer

from ..utils import is_admin, is_channel_member, schedule_delete, split_args


def register_vpn_handlers(
    router: Router,
    bot: Bot,
    vpn_issuer: VpnIssuer,
    outline_issuer: VpnIssuer | None,
    admin_user_ids: set[int],
    required_channel: str | None = None,
    required_channel_link: str | None = None,
    required_chat: str | None = None,
) -> None:
    @router.message(Command("vpn"))
    async def on_vpn(message: types.Message) -> None:
        if not message.from_user:
            return
        admin = await is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        )
        if required_chat and not admin:
            in_chat = await is_channel_member(bot, required_chat, message.from_user.id)
            if not in_chat:
                chat_link = f"https://t.me/{required_chat.lstrip('@')}"
                sent = await message.reply(
                    "VPN доступ только для участников чата: " + chat_link
                )
                schedule_delete(bot, sent)
                return
        if required_channel and not admin:
            member = await is_channel_member(
                bot, required_channel, message.from_user.id
            )
            if not member:
                link = (
                    required_channel_link
                    or f"https://t.me/{required_channel.lstrip('@')}"
                )
                sent = await message.reply(
                    "Для получения VPN подпишитесь на канал: " + link
                )
                schedule_delete(bot, sent)
                return
        access_key = await vpn_issuer.issue(message.from_user.id)
        sent = await message.reply(
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

    @router.message(Command("outline"))
    async def on_outline(message: types.Message) -> None:
        if not outline_issuer:
            sent = await message.reply("Outline не настроен.")
            schedule_delete(bot, sent)
            return
        if not message.from_user:
            return
        admin = await is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        )
        if required_chat and not admin:
            in_chat = await is_channel_member(bot, required_chat, message.from_user.id)
            if not in_chat:
                chat_link = f"https://t.me/{required_chat.lstrip('@')}"
                sent = await message.reply(
                    "VPN доступ только для участников чата: " + chat_link
                )
                schedule_delete(bot, sent)
                return
        if required_channel and not admin:
            member = await is_channel_member(
                bot, required_channel, message.from_user.id
            )
            if not member:
                link = (
                    required_channel_link
                    or f"https://t.me/{required_channel.lstrip('@')}"
                )
                sent = await message.reply(
                    "Для получения VPN подпишитесь на канал: " + link
                )
                schedule_delete(bot, sent)
                return
        access_key = await outline_issuer.issue(message.from_user.id)
        sent = await message.reply(
            "Ваш Outline ключ:\n"
            f"{access_key}\n\n"
            "Инструкция:\n"
            "1) Установите Outline Client\n"
            "2) Импортируйте ключ\n"
            "3) Нажмите Connect"
        )
        schedule_delete(bot, sent)

    @router.message(Command("vpn_revoke"))
    async def on_vpn_revoke(message: types.Message) -> None:
        if not message.from_user:
            return
        args = split_args(message.text or "")
        target_user_id = message.from_user.id
        if len(args) >= 2:
            if not await is_admin(
                bot, message.chat.id, message.from_user.id, admin_user_ids
            ):
                sent = await message.reply(
                    "Только администратор может отзывать чужие ключи."
                )
                schedule_delete(bot, sent)
                return
            try:
                target_user_id = int(args[1])
            except ValueError:
                sent = await message.reply("Неверный user_id.")
                schedule_delete(bot, sent)
                return
        await vpn_issuer.revoke(target_user_id)
        sent = await message.reply("Ключ отозван.")
        schedule_delete(bot, sent)

    @router.message(Command("outline_revoke"))
    async def on_outline_revoke(message: types.Message) -> None:
        if not outline_issuer:
            sent = await message.reply("Outline не настроен.")
            schedule_delete(bot, sent)
            return
        if not message.from_user:
            return
        args = split_args(message.text or "")
        target_user_id = message.from_user.id
        if len(args) >= 2:
            if not await is_admin(
                bot, message.chat.id, message.from_user.id, admin_user_ids
            ):
                sent = await message.reply(
                    "Только администратор может отзывать чужие ключи."
                )
                schedule_delete(bot, sent)
                return
            try:
                target_user_id = int(args[1])
            except ValueError:
                sent = await message.reply("Неверный user_id.")
                schedule_delete(bot, sent)
                return
        await outline_issuer.revoke(target_user_id)
        sent = await message.reply("Ключ отозван.")
        schedule_delete(bot, sent)

    @router.message(Command("vpn_stats"))
    async def on_vpn_stats(message: types.Message) -> None:
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
        stats = await vpn_issuer.stats()
        sent = await message.reply(
            "VPN статистика (Xray):\n"
            f"- всего ключей: {stats['total']}\n"
            f"- активные: {stats['active']}\n"
            f"- отозванные: {stats['revoked']}"
        )
        schedule_delete(bot, sent)

    @router.message(Command("outline_stats"))
    async def on_outline_stats(message: types.Message) -> None:
        if not outline_issuer:
            sent = await message.reply("Outline не настроен.")
            schedule_delete(bot, sent)
            return
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
        stats = await outline_issuer.stats()
        sent = await message.reply(
            "VPN статистика (Outline):\n"
            f"- всего ключей: {stats['total']}\n"
            f"- активные: {stats['active']}\n"
            f"- отозванные: {stats['revoked']}"
        )
        schedule_delete(bot, sent)

    @router.message(Command("vpn_users"))
    async def on_vpn_users(message: types.Message) -> None:
        if not message.from_user:
            return
        if not await is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        ):
            sent = await message.reply("Только администратор может смотреть список.")
            schedule_delete(bot, sent)
            return
        users = await vpn_issuer.active_users(limit=200)
        if not users:
            sent = await message.reply("Активных пользователей нет.")
            schedule_delete(bot, sent)
            return
        sent = await message.reply(
            "Активные пользователи:\n" + "\n".join(map(str, users))
        )
        schedule_delete(bot, sent)

    @router.message(Command("outline_users"))
    async def on_outline_users(message: types.Message) -> None:
        if not outline_issuer:
            sent = await message.reply("Outline не настроен.")
            schedule_delete(bot, sent)
            return
        if not message.from_user:
            return
        if not await is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        ):
            sent = await message.reply("Только администратор может смотреть список.")
            schedule_delete(bot, sent)
            return
        users = await outline_issuer.active_users(limit=200)
        if not users:
            sent = await message.reply("Активных пользователей нет.")
            schedule_delete(bot, sent)
            return
        sent = await message.reply(
            "Активные пользователи:\n" + "\n".join(map(str, users))
        )
        schedule_delete(bot, sent)
