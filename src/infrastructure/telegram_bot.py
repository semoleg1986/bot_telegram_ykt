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
    db_path: str | None = None,
    required_channel: str | None = None,
    required_channel_link: str | None = None,
    outline_api_url: str | None = None,
    outline_cert_sha256: str | None = None,
    vpn_ttl_days: int = 30,
    vpn_max_active_keys: int = 2,
    required_chat: str | None = None,
    market_data_urls: dict | None = None,
) -> Dispatcher:
    if not market_data_urls:
        market_data_urls = {}
    use_case, context_provider, policy_store, vpn_issuer, market = build_dependencies(
        bot=bot,
        policy=policy,
        admin_chat_id=admin_chat_id,
        db_path=db_path,
        outline_api_url=outline_api_url,
        outline_cert_sha256=outline_cert_sha256,
        ttl_days=vpn_ttl_days,
        max_active=vpn_max_active_keys,
        sber_url=market_data_urls.get("sber_url", ""),
        vtb_url=market_data_urls.get("vtb_url", ""),
        aeb_url=market_data_urls.get("aeb_url", ""),
        aosngs_url=market_data_urls.get("aosngs_url", ""),
        tuneft_urls=market_data_urls.get("tuneft_urls", ()),
    )
    router = build_router(
        use_case=use_case,
        bot=bot,
        context_provider=context_provider,
        policy_store=policy_store,
        vpn_issuer=vpn_issuer,
        market_data=market,
        admin_user_ids=set(admin_user_ids),
        required_channel=required_channel,
        required_channel_link=required_channel_link,
        required_chat=required_chat,
    )
    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def run_bot(
    token: str,
    policy: Policy,
    admin_chat_id: int | None = None,
    admin_user_ids: tuple[int, ...] = (),
    db_path: str | None = None,
    required_channel: str | None = None,
    required_channel_link: str | None = None,
    outline_api_url: str | None = None,
    outline_cert_sha256: str | None = None,
    vpn_ttl_days: int = 30,
    vpn_max_active_keys: int = 2,
    required_chat: str | None = None,
    market_data_urls: dict | None = None,
) -> None:
    bot = Bot(token=token)
    dispatcher = build_dispatcher(
        bot=bot,
        policy=policy,
        admin_chat_id=admin_chat_id,
        admin_user_ids=admin_user_ids,
        db_path=db_path,
        required_channel=required_channel,
        required_channel_link=required_channel_link,
        outline_api_url=outline_api_url,
        outline_cert_sha256=outline_cert_sha256,
        vpn_ttl_days=vpn_ttl_days,
        vpn_max_active_keys=vpn_max_active_keys,
        required_chat=required_chat,
        market_data_urls=market_data_urls,
    )

    await dispatcher.start_polling(bot)


def run_bot_sync(
    token: str,
    policy: Policy,
    admin_chat_id: int | None = None,
    admin_user_ids: tuple[int, ...] = (),
    db_path: str | None = None,
    required_channel: str | None = None,
    required_channel_link: str | None = None,
    outline_api_url: str | None = None,
    outline_cert_sha256: str | None = None,
    vpn_ttl_days: int = 30,
    vpn_max_active_keys: int = 2,
    required_chat: str | None = None,
    market_data_urls: dict | None = None,
) -> None:
    asyncio.run(
        run_bot(
            token,
            policy,
            admin_chat_id=admin_chat_id,
            admin_user_ids=admin_user_ids,
            db_path=db_path,
            required_channel=required_channel,
            required_channel_link=required_channel_link,
            outline_api_url=outline_api_url,
            outline_cert_sha256=outline_cert_sha256,
            vpn_ttl_days=vpn_ttl_days,
            vpn_max_active_keys=vpn_max_active_keys,
            required_chat=required_chat,
            market_data_urls=market_data_urls,
        )
    )
