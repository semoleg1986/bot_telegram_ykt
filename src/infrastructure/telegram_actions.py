from __future__ import annotations

from aiogram import Bot


class TelegramMessageAction:
    def __init__(self, bot: Bot, admin_chat_id: int | None = None) -> None:
        self._bot = bot
        self._admin_chat_id = admin_chat_id

    async def delete_message(self, chat_id: int, message_id: int) -> None:
        try:
            await self._bot.delete_message(chat_id, message_id)
        except Exception:
            # Message might already be deleted or not allowed to delete
            return

    async def notify_admins(self, chat_id: int, text: str) -> None:
        target_chat_id = self._admin_chat_id or chat_id
        await self._bot.send_message(target_chat_id, text)
