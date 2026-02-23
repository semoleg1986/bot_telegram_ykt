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
from src.infrastructure.clients.outline_client import OutlineClient
from src.infrastructure.persistence.context_provider import SQLiteContextProvider
from src.infrastructure.persistence.db import SQLiteDatabase
from src.infrastructure.persistence.decision_logger import SQLiteDecisionLogger
from src.infrastructure.persistence.policy_store import SQLitePolicyStore
from src.infrastructure.persistence.vpn_issuer import OutlineVpnIssuer, SQLiteVpnIssuer
from src.infrastructure.telegram_actions import TelegramMessageAction


def build_dependencies(
    bot: Bot,
    policy: Policy,
    admin_chat_id: int | None = None,
    db_path: str | None = None,
    outline_api_url: str | None = None,
    outline_cert_sha256: str | None = None,
    ttl_days: int = 30,
    max_active: int = 2,
) -> tuple[ProcessMessage, ContextProvider, PolicyStore, VpnIssuer]:
    if db_path:
        database = SQLiteDatabase(db_path)
        context_provider = SQLiteContextProvider(database)
        logger = SQLiteDecisionLogger(database)
        policy_store = SQLitePolicyStore(database, initial_policy=policy.normalized())
        if outline_api_url:
            client = OutlineClient(
                api_url=outline_api_url, cert_sha256=outline_cert_sha256
            )
            vpn_issuer = OutlineVpnIssuer(
                database, client, ttl_days=ttl_days, max_active=max_active
            )
        else:
            vpn_issuer = SQLiteVpnIssuer(
                database, ttl_days=ttl_days, max_active=max_active
            )
    else:
        context_provider = InMemoryContextProvider()
        logger = InMemoryDecisionLogger()
        policy_store = InMemoryPolicyStore(policy=policy.normalized())
        vpn_issuer = StubVpnIssuer()
    actions = TelegramMessageAction(bot, admin_chat_id=admin_chat_id)
    use_case = ProcessMessage(
        policy_store=policy_store,
        context_provider=context_provider,
        logger=logger,
        actions=actions,
        notify_on_delete=True,
    )
    return use_case, context_provider, policy_store, vpn_issuer
