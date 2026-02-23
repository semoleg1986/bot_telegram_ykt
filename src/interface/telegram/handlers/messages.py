from __future__ import annotations

from aiogram import Bot, Router, types

from src.application import ProcessMessage
from src.domain import Message, User

from ..utils import extract_urls, is_admin, is_channel_member


def register_message_handler(
    router: Router,
    bot: Bot,
    use_case: ProcessMessage,
    context_provider,
    admin_user_ids: set[int],
    required_channel: str | None = None,
    required_channel_link: str | None = None,
) -> None:
    @router.message()
    async def on_message(message: types.Message) -> None:
        if not message.from_user:
            return
        text = message.text or message.caption or ""
        urls = extract_urls(message.text, message.entities)
        urls += extract_urls(message.caption, message.caption_entities)

        domain_message = Message.from_text(
            message_id=message.message_id,
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            text=text,
        ).with_urls(urls)

        if text:
            context_provider.add_text(message.chat.id, message.from_user.id, text)

        admin = await is_admin(
            bot, message.chat.id, message.from_user.id, admin_user_ids
        )
        user = User(user_id=message.from_user.id, is_admin=admin)

        if required_channel and not admin:
            is_member = await is_channel_member(
                bot, required_channel, message.from_user.id
            )
            if not is_member:
                try:
                    await bot.delete_message(message.chat.id, message.message_id)
                except Exception:
                    pass
                link = (
                    required_channel_link
                    or f"https://t.me/{required_channel.lstrip('@')}"
                )
                try:
                    await bot.send_message(
                        message.chat.id,
                        "Чтобы писать в чате, подпишитесь на канал: " + link,
                    )
                except Exception:
                    pass
                return

        result = await use_case.execute(domain_message, user)
        if result.decision == "deleted":
            display = (
                f"@{message.from_user.username}"
                if message.from_user.username
                else message.from_user.full_name
            )
            try:
                await bot.send_message(
                    message.chat.id,
                    f"Предупреждение для {display}. Причина: Нарушение правил чата",
                )
            except Exception:
                pass
