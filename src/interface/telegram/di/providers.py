from __future__ import annotations

from aiogram import Bot

from src.application import ContextProvider, PolicyStore, ProcessMessage
from src.domain import Policy
from src.infrastructure import (
    InMemoryContextProvider,
    InMemoryDecisionLogger,
    InMemoryPolicyStore,
)
from src.infrastructure.clients.market_data import MarketDataService
from src.infrastructure.persistence.cache import SQLiteCache
from src.infrastructure.persistence.context_provider import SQLiteContextProvider
from src.infrastructure.persistence.db import SQLiteDatabase
from src.infrastructure.persistence.decision_logger import SQLiteDecisionLogger
from src.infrastructure.persistence.policy_store import SQLitePolicyStore
from src.infrastructure.telegram_actions import TelegramMessageAction


def build_dependencies(
    bot: Bot,
    policy: Policy,
    admin_chat_id: int | None = None,
    db_path: str | None = None,
    sber_url: str = "",
    vtb_url: str = "",
    aeb_url: str = "",
    aosngs_url: str = "",
    tuneft_urls: tuple[str, ...] = (),
) -> tuple[ProcessMessage, ContextProvider, PolicyStore, MarketDataService,]:
    if db_path:
        database = SQLiteDatabase(db_path)
        context_provider = SQLiteContextProvider(database)
        logger = SQLiteDecisionLogger(database)
        policy_store = SQLitePolicyStore(database, initial_policy=policy.normalized())
        cache = SQLiteCache(database)
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
    return use_case, context_provider, policy_store, market
