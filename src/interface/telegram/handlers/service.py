from __future__ import annotations

import asyncio

from aiogram import Router, types
from aiogram.filters import Command

from src.infrastructure.clients.market_data import MarketDataService

from ..utils import schedule_delete


def _format_rates_table(data: dict) -> str:
    banks = data.get("banks", {})
    header = "Банк | USD | EUR | CNY"
    rows = [header, "-" * len(header)]
    for bank in ("Сбер", "ВТБ", "АЭБ"):
        rates = banks.get(bank, {})
        usd = "—"
        eur = "—"
        cny = "—"
        if "USD" in rates:
            usd = f"{rates['USD'][0]}/{rates['USD'][1]}"
        if "EUR" in rates:
            eur = f"{rates['EUR'][0]}/{rates['EUR'][1]}"
        if "CNY" in rates:
            cny = f"{rates['CNY'][0]}/{rates['CNY'][1]}"
        rows.append(f"{bank} | {usd} | {eur} | {cny}")
    return "```\n" + "\n".join(rows) + "\n```"


def _format_fuel_table(data: dict) -> str:
    companies = data.get("companies", {})
    header = "Компания | АИ-92 | АИ-95 | ДТ"
    rows = [header, "-" * len(header)]
    for company in ("Саханефтегазсбыт", "Туймаада-Нефть", "ЯТЭК"):
        prices = companies.get(company, {})
        rows.append(
            f"{company} | {prices.get('AI-92', '—')} | "
            f"{prices.get('AI-95', '—')} | {prices.get('DT', '—')}"
        )
    return "```\n" + "\n".join(rows) + "\n```"


def register_service_handlers(router: Router, market: MarketDataService) -> None:
    @router.message(Command("rates"))
    async def on_rates(message: types.Message) -> None:
        data = await asyncio.to_thread(market.get_rates)
        sent = await message.reply(_format_rates_table(data), parse_mode="Markdown")
        schedule_delete(message.bot, sent)

    @router.message(Command("fuel"))
    async def on_fuel(message: types.Message) -> None:
        data = await asyncio.to_thread(market.get_fuel)
        sent = await message.reply(_format_fuel_table(data), parse_mode="Markdown")
        schedule_delete(message.bot, sent)
