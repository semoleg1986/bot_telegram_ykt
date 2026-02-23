from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher

from src.domain import Policy
from src.interface.telegram.app import build_router
from src.interface.telegram.di import build_dependencies


def build_dispatcher(
    bot: Bot,
    policy: Policy,
    admin_chat_id: int | None = None,
    admin_user_ids: tuple[int, ...] = (),
) -> Dispatcher:
    use_case, context_provider, policy_store, vpn_issuer = build_dependencies(
        bot=bot, policy=policy, admin_chat_id=admin_chat_id
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
    dispatcher = build_dispatcher(
        bot=bot,
        policy=policy,
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
