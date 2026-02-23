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
    )


if __name__ == "__main__":
    main()
