from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from html import unescape
from typing import Any

from src.infrastructure.persistence.cache import SQLiteCache

_NUM_RE = re.compile(r"\d+[.,]\d+")
_TAG_RE = re.compile(r"<[^>]+>")


def _fetch_text(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _strip_tags(html: str) -> str:
    cleaned = _TAG_RE.sub(" ", unescape(html))
    cleaned = cleaned.replace("\xa0", " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def _pick_buy_sell(numbers: list[str]) -> tuple[str, str] | None:
    if len(numbers) < 2:
        return None
    if len(numbers) >= 3:
        return numbers[-2], numbers[-1]
    return numbers[0], numbers[1]


def _find_numbers_after(text: str, pattern: str, limit: int = 160) -> list[str]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return []
    start = match.end()
    chunk = text[start : start + limit]
    return _NUM_RE.findall(chunk)


def _extract_block(text: str, start: str, end: str) -> str:
    lower = text.lower()
    start_idx = lower.find(start.lower())
    if start_idx == -1:
        return text
    end_idx = lower.find(end.lower(), start_idx)
    if end_idx == -1:
        return text[start_idx:]
    return text[start_idx:end_idx]


def _parse_bankiros_rates(raw_html: str) -> dict[str, dict[str, Any]]:
    text = _strip_tags(raw_html)
    block = _extract_block(text, "Курсы «", "ЦБ РФ")
    if block == text:
        block = _extract_block(text, "Курсы", "Лучшие курсы")
    if block == text:
        block = _extract_block(text, "Курсы", "Мосбиржа")
    rates: dict[str, dict[str, Any]] = {}
    for code in ("USD", "EUR", "CNY"):
        match = re.search(
            rf"\\b{code}\\b\\s*([0-9.,]+)\\s*([0-9.,]+)",
            block,
            flags=re.IGNORECASE,
        )
        if not match:
            match = re.search(
                rf"\\b{code}\\b[^0-9]{{0,60}}([0-9.,]+)[^0-9]{{0,60}}([0-9.,]+)",
                block,
                flags=re.IGNORECASE,
            )
        if match:
            rates[code] = {"buy": match.group(1), "sell": match.group(2), "unit": 1}
            continue
        numbers = _find_numbers_after(block, rf"\\b{code}\\b")
        picked = _pick_buy_sell(numbers)
        if picked:
            rates[code] = {"buy": picked[0], "sell": picked[1], "unit": 1}
    return rates


def _parse_aeb_rates(raw_html: str) -> dict[str, dict[str, Any]]:
    text = _strip_tags(raw_html)
    rates: dict[str, dict[str, Any]] = {}
    for code in ("USD", "EUR"):
        patterns = (
            rf"{code}.{{0,120}}?(?:покуп|buy)[^0-9]*([0-9.,]+)"
            rf".{{0,80}}?(?:прод|sell)[^0-9]*([0-9.,]+)",
            rf"{code}.{{0,120}}?([0-9.,]+).{{0,40}}?([0-9.,]+)",
        )
        found = None
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                found = (match.group(1), match.group(2))
                break
        if not found:
            numbers = _find_numbers_after(text, rf"\\b{code}\\b")
            found = _pick_buy_sell(numbers)
        if found:
            rates[code] = {"buy": found[0], "sell": found[1], "unit": 1}

    cny_numbers = _find_numbers_after(text, r"\\bCNY\\b")
    picked = _pick_buy_sell(cny_numbers)
    if picked:
        unit = 10 if re.search(r"\\b10\\s*CNY\\b", text, re.IGNORECASE) else 1
        rates["CNY"] = {"buy": picked[0], "sell": picked[1], "unit": unit}
    return rates


def _parse_aosngs_prices(raw_html: str) -> dict[str, str]:
    prices: dict[str, str] = {}
    tag_patterns = (
        (r"block__title\">\\s*92\\s*<", "AI-92"),
        (r"block__title\">\\s*95\\s*<", "AI-95"),
        (r"block__title\">\\s*ДТ\\s*<", "DT"),
    )
    for pattern, key in tag_patterns:
        match = re.search(
            pattern + r".{0,120}?block__price\">\\s*([0-9.,]+)",
            raw_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            prices[key] = match.group(1)

    if prices:
        return prices

    text = _strip_tags(raw_html)
    patterns = (
        (r"АИ-?92|\\b92\\b", "AI-92"),
        (r"АИ-?95|\\b95\\b", "AI-95"),
        (r"\\bДТ\\b|ДИЗ|DIESEL", "DT"),
    )
    for pattern, key in patterns:
        numbers = _find_numbers_after(text, pattern, limit=80)
        if numbers:
            prices[key] = numbers[0]
    return prices


def _parse_tuneft_json(data: Any) -> dict[str, str]:
    prices: dict[str, str] = {}
    if isinstance(data, dict):
        items = data.get("prices") or data.get("items") or data.get("data")
    else:
        items = data
    if not isinstance(items, list):
        return prices
    for item in items:
        name = str(item.get("name") or item.get("title") or "").upper()
        value = item.get("price") or item.get("value")
        if value is None:
            continue
        value = str(value).replace(",", ".")
        if "92" in name and "AI-92" not in prices:
            prices["AI-92"] = value
        if "95" in name and "AI-95" not in prices:
            prices["AI-95"] = value
        if "ДТ" in name or "DIESEL" in name or "ДИЗ" in name:
            prices["DT"] = value
    return prices


@dataclass
class MarketDataService:
    cache: SQLiteCache
    sber_url: str
    vtb_url: str
    aeb_url: str
    aosngs_url: str
    tuneft_urls: tuple[str, ...]
    ttl_sec: int = 3600

    def get_rates(self) -> dict[str, Any]:
        cached = self.cache.get("rates", self.ttl_sec)
        if cached:
            return cached

        result: dict[str, Any] = {"banks": {}}
        try:
            sber_html = _fetch_text(self.sber_url)
            result["banks"]["Сбер"] = _parse_bankiros_rates(sber_html)
        except Exception:
            result["banks"]["Сбер"] = {}
        try:
            vtb_html = _fetch_text(self.vtb_url)
            result["banks"]["ВТБ"] = _parse_bankiros_rates(vtb_html)
        except Exception:
            result["banks"]["ВТБ"] = {}
        try:
            aeb_html = _fetch_text(self.aeb_url)
            result["banks"]["АЭБ"] = _parse_aeb_rates(aeb_html)
        except Exception:
            result["banks"]["АЭБ"] = {}

        if any(result["banks"].get(bank) for bank in result["banks"]):
            self.cache.set("rates", result)
        return result

    def get_fuel(self) -> dict[str, Any]:
        cached = self.cache.get("fuel", self.ttl_sec)
        if cached:
            return cached

        result: dict[str, Any] = {"companies": {}}
        try:
            aos_html = _fetch_text(self.aosngs_url)
            result["companies"]["Саханефтегазсбыт"] = _parse_aosngs_prices(aos_html)
        except Exception:
            result["companies"]["Саханефтегазсбыт"] = {}

        tuneft_prices: dict[str, str] = {}
        for url in self.tuneft_urls:
            try:
                raw = _fetch_text(url)
                data = json.loads(raw)
                tuneft_prices = _parse_tuneft_json(data)
                if tuneft_prices:
                    break
            except Exception:
                continue
        result["companies"]["Туймаада-Нефть"] = tuneft_prices

        if any(result["companies"].get(company) for company in result["companies"]):
            self.cache.set("fuel", result)
        return result
