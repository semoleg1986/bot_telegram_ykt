from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command

from src.application import VpnIssuer


def register_vpn_handlers(router: Router, vpn_issuer: VpnIssuer) -> None:
    @router.message(Command("vpn"))
    async def on_vpn(message: types.Message) -> None:
        if not message.from_user:
            return
        access_key = await vpn_issuer.issue(message.from_user.id)
        await message.reply(f"Ваш Outline ключ: {access_key}")
