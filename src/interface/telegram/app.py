from __future__ import annotations

from aiogram import Bot, Router

from src.application import PolicyStore, ProcessMessage, VpnIssuer

from .handlers.messages import register_message_handler
from .handlers.meta import register_meta_handlers
from .handlers.spam import register_spam_handlers
from .handlers.vpn import register_vpn_handlers


def build_router(
    use_case: ProcessMessage,
    bot: Bot,
    context_provider,
    policy_store: PolicyStore,
    vpn_issuer: VpnIssuer,
    admin_user_ids: set[int],
) -> Router:
    router = Router()
    register_spam_handlers(router, bot, policy_store, admin_user_ids)
    register_vpn_handlers(router, vpn_issuer)
    register_meta_handlers(router, bot, admin_user_ids)
    register_message_handler(router, bot, use_case, context_provider, admin_user_ids)
    return router
