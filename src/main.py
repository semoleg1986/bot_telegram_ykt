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
        xray_host=settings.xray_host,
        xray_port=settings.xray_port,
        xray_uuid=settings.xray_uuid,
        xray_public_key=settings.xray_public_key,
        xray_sni=settings.xray_sni,
        xray_short_id=settings.xray_short_id,
        xray_profile_name=settings.xray_profile_name,
        xray_fingerprint=settings.xray_fingerprint,
        xray_alpn=settings.xray_alpn,
        xray_flow=settings.xray_flow,
        xray_path=settings.xray_path,
        vpn_ttl_days=settings.vpn_ttl_days,
        vpn_max_active_keys=settings.vpn_max_active_keys,
        required_chat=settings.required_chat,
        market_data_urls={
            "sber_url": settings.sber_rates_url,
            "vtb_url": settings.vtb_rates_url,
            "aeb_url": settings.aeb_rates_url,
            "aosngs_url": settings.aosngs_url,
            "tuneft_urls": settings.tuneft_urls,
        },
    )


if __name__ == "__main__":
    main()
