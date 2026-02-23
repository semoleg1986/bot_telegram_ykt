from __future__ import annotations

from aiogram import Bot, Router, types
from aiogram.filters import Command

from ..utils import is_admin


def register_meta_handlers(router: Router, bot: Bot, admin_user_ids: set[int]) -> None:
    @router.message(Command("whoami"))
    async def on_whoami(message: types.Message) -> None:
        if not message.from_user:
            return
        admin = await is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        )
        await message.reply(
            (
                f"user_id={message.from_user.id}, "
                f"chat_id={message.chat.id}, admin={admin}"
            )
        )

    @router.message(Command("help"))
    async def on_help(message: types.Message) -> None:
        await message.reply(
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
            "/whoami"
        )
