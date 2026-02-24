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


def _fetch_text(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", unescape(html))).strip()


def _parse_bankiros_rates(text: str) -> dict[str, tuple[str, str]]:
    rates: dict[str, tuple[str, str]] = {}
    for code in ("USD", "EUR", "CNY"):
        pattern = rf"{code}\\s*\\|?\\s*(\\d+[.,]\\d+)\\s*\\|?\\s*(\\d+[.,]\\d+)"
        match = re.search(pattern, text)
        if match:
            rates[code] = (match.group(1), match.group(2))
    return rates


def _parse_aeb_rates(text: str) -> dict[str, tuple[str, str]]:
    rates: dict[str, tuple[str, str]] = {}
    for code in ("USD", "EUR", "CNY"):
        pattern = rf"{code}\\s*\\|?\\s*(\\d+[.,]\\d+)\\s*\\|?\\s*(\\d+[.,]\\d+)"
        match = re.search(pattern, text)
        if match:
            rates[code] = (match.group(1), match.group(2))
    return rates


def _parse_aosngs_prices(text: str) -> dict[str, str]:
    prices: dict[str, str] = {}
    for label, key in (("92", "AI-92"), ("95", "AI-95"), ("ДТ", "DT")):
        match = re.search(
            rf"\\b{label}\\b\\s*(\\d+[.,]\\d+)",
            text,
        )
        if not match:
            match = re.search(
                rf"\\b{label}\\b\\s*(\\d+[.,]\\d+)\\s*₽",
                text,
            )
        if match:
            prices[key] = match.group(1)
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
            sber_text = _strip_tags(_fetch_text(self.sber_url))
            result["banks"]["Сбер"] = _parse_bankiros_rates(sber_text)
        except Exception:
            result["banks"]["Сбер"] = {}
        try:
            vtb_text = _strip_tags(_fetch_text(self.vtb_url))
            result["banks"]["ВТБ"] = _parse_bankiros_rates(vtb_text)
        except Exception:
            result["banks"]["ВТБ"] = {}
        try:
            aeb_text = _strip_tags(_fetch_text(self.aeb_url))
            result["banks"]["АЭБ"] = _parse_aeb_rates(aeb_text)
        except Exception:
            result["banks"]["АЭБ"] = {}

        self.cache.set("rates", result)
        return result

    def get_fuel(self) -> dict[str, Any]:
        cached = self.cache.get("fuel", self.ttl_sec)
        if cached:
            return cached

        result: dict[str, Any] = {"companies": {}}
        try:
            aos_text = _strip_tags(_fetch_text(self.aosngs_url))
            result["companies"]["Саханефтегазсбыт"] = _parse_aosngs_prices(aos_text)
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

        self.cache.set("fuel", result)
        return result
