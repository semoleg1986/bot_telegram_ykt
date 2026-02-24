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
    xray_host: str | None = None,
    xray_port: int | None = None,
    xray_uuid: str | None = None,
    xray_public_key: str | None = None,
    xray_sni: str | None = None,
    xray_short_id: str | None = None,
    xray_profile_name: str = "Yakutsk VPN",
    xray_fingerprint: str = "chrome",
    xray_alpn: str = "h2",
    xray_flow: str = "xtls-rprx-vision",
    xray_path: str = "/",
    vpn_ttl_days: int = 30,
    vpn_max_active_keys: int = 2,
    required_chat: str | None = None,
    market_data_urls: dict | None = None,
) -> Dispatcher:
    if not market_data_urls:
        market_data_urls = {}
    (
        use_case,
        context_provider,
        policy_store,
        vpn_issuer,
        outline_issuer,
        market,
    ) = build_dependencies(
        bot=bot,
        policy=policy,
        admin_chat_id=admin_chat_id,
        db_path=db_path,
        outline_api_url=outline_api_url,
        outline_cert_sha256=outline_cert_sha256,
        xray_host=xray_host,
        xray_port=xray_port,
        xray_uuid=xray_uuid,
        xray_public_key=xray_public_key,
        xray_sni=xray_sni,
        xray_short_id=xray_short_id,
        xray_profile_name=xray_profile_name,
        xray_fingerprint=xray_fingerprint,
        xray_alpn=xray_alpn,
        xray_flow=xray_flow,
        xray_path=xray_path,
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
        outline_issuer=outline_issuer,
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
    xray_host: str | None = None,
    xray_port: int | None = None,
    xray_uuid: str | None = None,
    xray_public_key: str | None = None,
    xray_sni: str | None = None,
    xray_short_id: str | None = None,
    xray_profile_name: str = "Yakutsk VPN",
    xray_fingerprint: str = "chrome",
    xray_alpn: str = "h2",
    xray_flow: str = "xtls-rprx-vision",
    xray_path: str = "/",
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
        xray_host=xray_host,
        xray_port=xray_port,
        xray_uuid=xray_uuid,
        xray_public_key=xray_public_key,
        xray_sni=xray_sni,
        xray_short_id=xray_short_id,
        xray_profile_name=xray_profile_name,
        xray_fingerprint=xray_fingerprint,
        xray_alpn=xray_alpn,
        xray_flow=xray_flow,
        xray_path=xray_path,
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
    xray_host: str | None = None,
    xray_port: int | None = None,
    xray_uuid: str | None = None,
    xray_public_key: str | None = None,
    xray_sni: str | None = None,
    xray_short_id: str | None = None,
    xray_profile_name: str = "Yakutsk VPN",
    xray_fingerprint: str = "chrome",
    xray_alpn: str = "h2",
    xray_flow: str = "xtls-rprx-vision",
    xray_path: str = "/",
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
            xray_host=xray_host,
            xray_port=xray_port,
            xray_uuid=xray_uuid,
            xray_public_key=xray_public_key,
            xray_sni=xray_sni,
            xray_short_id=xray_short_id,
            xray_profile_name=xray_profile_name,
            xray_fingerprint=xray_fingerprint,
            xray_alpn=xray_alpn,
            xray_flow=xray_flow,
            xray_path=xray_path,
            vpn_ttl_days=vpn_ttl_days,
            vpn_max_active_keys=vpn_max_active_keys,
            required_chat=required_chat,
            market_data_urls=market_data_urls,
        )
    )
