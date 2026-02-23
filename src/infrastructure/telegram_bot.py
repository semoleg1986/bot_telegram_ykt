from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher

from src.application import ProcessMessage
from src.domain import Policy
from src.infrastructure import (
    InMemoryContextProvider,
    InMemoryDecisionLogger,
    InMemoryPolicyStore,
    StubVpnIssuer,
)
from src.interface.telegram_handlers import build_router


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


def build_dispatcher(
    bot: Bot,
    policy: Policy,
    context_provider: InMemoryContextProvider,
    logger: InMemoryDecisionLogger,
    admin_chat_id: int | None = None,
    admin_user_ids: tuple[int, ...] = (),
) -> Dispatcher:
    actions = TelegramMessageAction(bot, admin_chat_id=admin_chat_id)
    policy_store = InMemoryPolicyStore(policy=policy.normalized())
    vpn_issuer = StubVpnIssuer()
    use_case = ProcessMessage(
        policy_store=policy_store,
        context_provider=context_provider,
        logger=logger,
        actions=actions,
        notify_on_delete=True,
    )
    router = build_router(
        use_case=use_case,
        bot=bot,
        context_provider=context_provider,
        policy_store=policy_store,
        vpn_issuer=vpn_issuer,
        admin_user_ids=set(admin_user_ids),
    )
    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def run_bot(
    token: str,
    policy: Policy,
    admin_chat_id: int | None = None,
    admin_user_ids: tuple[int, ...] = (),
) -> None:
    bot = Bot(token=token)
    context = InMemoryContextProvider()
    logger = InMemoryDecisionLogger()
    dispatcher = build_dispatcher(
        bot=bot,
        policy=policy,
        context_provider=context,
        logger=logger,
        admin_chat_id=admin_chat_id,
        admin_user_ids=admin_user_ids,
    )

    await dispatcher.start_polling(bot)


def run_bot_sync(
    token: str,
    policy: Policy,
    admin_chat_id: int | None = None,
    admin_user_ids: tuple[int, ...] = (),
) -> None:
    asyncio.run(
        run_bot(
            token, policy, admin_chat_id=admin_chat_id, admin_user_ids=admin_user_ids
        )
    )
