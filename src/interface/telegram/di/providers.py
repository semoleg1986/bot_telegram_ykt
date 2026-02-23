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
from src.infrastructure.sqlite_store import (
    SQLiteContextProvider,
    SQLiteDatabase,
    SQLiteDecisionLogger,
    SQLitePolicyStore,
    SQLiteVpnIssuer,
)
from src.infrastructure.telegram_actions import TelegramMessageAction


def build_dependencies(
    bot: Bot,
    policy: Policy,
    admin_chat_id: int | None = None,
    db_path: str | None = None,
) -> tuple[ProcessMessage, ContextProvider, PolicyStore, VpnIssuer]:
    if db_path:
        database = SQLiteDatabase(db_path)
        context_provider = SQLiteContextProvider(database)
        logger = SQLiteDecisionLogger(database)
        policy_store = SQLitePolicyStore(database, initial_policy=policy.normalized())
        vpn_issuer = SQLiteVpnIssuer(database)
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
