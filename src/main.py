from __future__ import annotations

from src.infrastructure.config import build_policy, load_settings
from src.infrastructure.telegram_bot import run_bot_sync


def main() -> None:
    settings = load_settings()
    policy = build_policy(settings)
    run_bot_sync(
        token=settings.token,
        policy=policy,
        admin_chat_id=settings.admin_chat_id,
        admin_user_ids=settings.admin_user_ids,
        db_path=settings.db_path,
        required_channel=settings.required_channel,
        required_channel_link=settings.required_channel_link,
        outline_api_url=settings.outline_api_url,
        outline_cert_sha256=settings.outline_cert_sha256,
        vpn_ttl_days=settings.vpn_ttl_days,
        vpn_max_active_keys=settings.vpn_max_active_keys,
        required_chat=settings.required_chat,
    )


if __name__ == "__main__":
    main()
