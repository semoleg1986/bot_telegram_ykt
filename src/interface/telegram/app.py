from __future__ import annotations

from aiogram import Bot, Router

from src.application import PolicyStore, ProcessMessage, VpnIssuer

from .handlers.menu import register_menu_handlers
from .handlers.messages import register_message_handler
from .handlers.meta import register_meta_handlers
from .handlers.service import register_service_handlers
from .handlers.spam import register_spam_handlers
from .handlers.vpn import register_vpn_handlers


def build_router(
    use_case: ProcessMessage,
    bot: Bot,
    context_provider,
    policy_store: PolicyStore,
    vpn_issuer: VpnIssuer,
    outline_issuer: VpnIssuer | None,
    market_data,
    admin_user_ids: set[int],
    required_channel: str | None = None,
    required_channel_link: str | None = None,
    required_chat: str | None = None,
) -> Router:
    router = Router()
    register_spam_handlers(router, bot, policy_store, admin_user_ids)
    register_vpn_handlers(
        router,
        bot,
        vpn_issuer,
        outline_issuer,
        admin_user_ids,
        required_channel=required_channel,
        required_channel_link=required_channel_link,
        required_chat=required_chat,
    )
    register_meta_handlers(router, bot, admin_user_ids)
    register_menu_handlers(
        router,
        bot,
        policy_store,
        vpn_issuer,
        outline_issuer,
        market_data,
        admin_user_ids,
        required_channel=required_channel,
        required_channel_link=required_channel_link,
        required_chat=required_chat,
    )
    register_service_handlers(router, market_data)
    register_message_handler(
        router,
        bot,
        use_case,
        context_provider,
        admin_user_ids,
        required_channel=required_channel,
        required_channel_link=required_channel_link,
    )
    return router
