from __future__ import annotations

from aiogram import Bot

from src.application import ContextProvider, PolicyStore, ProcessMessage, VpnIssuer
from src.domain import Policy
from src.infrastructure import (
    InMemoryContextProvider,
    InMemoryDecisionLogger,
    InMemoryPolicyStore,
    StubVpnIssuer,
)
from src.infrastructure.clients.market_data import MarketDataService
from src.infrastructure.clients.outline_client import OutlineClient
from src.infrastructure.persistence.cache import SQLiteCache
from src.infrastructure.persistence.context_provider import SQLiteContextProvider
from src.infrastructure.persistence.db import SQLiteDatabase
from src.infrastructure.persistence.decision_logger import SQLiteDecisionLogger
from src.infrastructure.persistence.policy_store import SQLitePolicyStore
from src.infrastructure.persistence.vpn_issuer import (
    OutlineVpnIssuer,
    SQLiteVpnIssuer,
    XrayVpnIssuer,
)
from src.infrastructure.telegram_actions import TelegramMessageAction
from src.infrastructure.vpn import XrayProfile


def build_dependencies(
    bot: Bot,
    policy: Policy,
    admin_chat_id: int | None = None,
    db_path: str | None = None,
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
    ttl_days: int = 30,
    max_active: int = 2,
    sber_url: str = "",
    vtb_url: str = "",
    aeb_url: str = "",
    aosngs_url: str = "",
    tuneft_urls: tuple[str, ...] = (),
) -> tuple[
    ProcessMessage,
    ContextProvider,
    PolicyStore,
    VpnIssuer,
    VpnIssuer | None,
    MarketDataService,
]:
    if db_path:
        database = SQLiteDatabase(db_path)
        context_provider = SQLiteContextProvider(database)
        logger = SQLiteDecisionLogger(database)
        policy_store = SQLitePolicyStore(database, initial_policy=policy.normalized())
        cache = SQLiteCache(database)
        outline_issuer: VpnIssuer | None = None
        if outline_api_url:
            client = OutlineClient(
                api_url=outline_api_url, cert_sha256=outline_cert_sha256
            )
            outline_issuer = OutlineVpnIssuer(
                database, client, ttl_days=ttl_days, max_active=max_active
            )
        has_xray = all(
            [
                xray_host,
                xray_port,
                xray_uuid,
                xray_public_key,
                xray_sni,
                xray_short_id,
            ]
        )
        if has_xray:
            profile = XrayProfile(
                host=xray_host or "",
                port=int(xray_port or 0),
                uuid=xray_uuid or "",
                public_key=xray_public_key or "",
                sni=xray_sni or "",
                short_id=xray_short_id or "",
                name=xray_profile_name,
                fingerprint=xray_fingerprint,
                alpn=xray_alpn,
                flow=xray_flow,
                path=xray_path,
            )
            vpn_issuer = XrayVpnIssuer(
                database, profile, ttl_days=ttl_days, max_active=max_active
            )
        elif outline_issuer:
            vpn_issuer = outline_issuer
        else:
            vpn_issuer = SQLiteVpnIssuer(
                database, ttl_days=ttl_days, max_active=max_active
            )
        market = MarketDataService(
            cache=cache,
            sber_url=sber_url,
            vtb_url=vtb_url,
            aeb_url=aeb_url,
            aosngs_url=aosngs_url,
            tuneft_urls=tuneft_urls,
        )
    else:
        context_provider = InMemoryContextProvider()
        logger = InMemoryDecisionLogger()
        policy_store = InMemoryPolicyStore(policy=policy.normalized())
        vpn_issuer = StubVpnIssuer()
        outline_issuer = None
        memory_db = SQLiteDatabase(":memory:")
        cache = SQLiteCache(memory_db)
        market = MarketDataService(
            cache=cache,
            sber_url=sber_url,
            vtb_url=vtb_url,
            aeb_url=aeb_url,
            aosngs_url=aosngs_url,
            tuneft_urls=tuneft_urls,
        )
    actions = TelegramMessageAction(bot, admin_chat_id=admin_chat_id)
    use_case = ProcessMessage(
        policy_store=policy_store,
        context_provider=context_provider,
        logger=logger,
        actions=actions,
        notify_on_delete=False,
    )
    return use_case, context_provider, policy_store, vpn_issuer, outline_issuer, market
