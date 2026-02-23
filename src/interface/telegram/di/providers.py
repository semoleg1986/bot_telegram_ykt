from __future__ import annotations

from aiogram import Bot

from src.application import ProcessMessage
from src.domain import Policy
from src.infrastructure import (
    InMemoryContextProvider,
    InMemoryDecisionLogger,
    InMemoryPolicyStore,
    StubVpnIssuer,
)
from src.infrastructure.telegram_actions import TelegramMessageAction


def build_dependencies(
    bot: Bot, policy: Policy, admin_chat_id: int | None = None
) -> tuple[ProcessMessage, InMemoryContextProvider, InMemoryPolicyStore, StubVpnIssuer]:
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
