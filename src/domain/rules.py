from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

from .decision import RuleMatch
from .models import Message
from .policy import Policy


def _extract_domains(urls: Iterable[str]) -> tuple[str, ...]:
    domains: list[str] = []
    for raw in urls:
        try:
            parsed = urlparse(raw)
            host = parsed.hostname or ""
            if host:
                domains.append(host.lower())
        except ValueError:
            continue
    return tuple(domains)


@dataclass(frozen=True)
class RuleResult:
    matched: bool
    match: RuleMatch | None = None


def rule_blocklisted_domain(message: Message, policy: Policy) -> RuleResult:
    domains = _extract_domains(message.urls)
    for domain in domains:
        if any(
            domain == blocked or domain.endswith(f".{blocked}")
            for blocked in policy.domain_blacklist
        ):
            return RuleResult(
                True, RuleMatch("domain_blacklist", f"Запрещенный домен: {domain}")
            )
    return RuleResult(False)


def rule_whitelisted_domain(message: Message, policy: Policy) -> RuleResult:
    domains = _extract_domains(message.urls)
    for domain in domains:
        if any(
            domain == allowed or domain.endswith(f".{allowed}")
            for allowed in policy.domain_whitelist
        ):
            return RuleResult(
                True, RuleMatch("domain_whitelist", f"Разрешенный домен: {domain}")
            )
    return RuleResult(False)


def rule_keyword_match(message: Message, policy: Policy) -> RuleResult:
    text = message.text.lower()
    for keyword in policy.keyword_list:
        if keyword and keyword in text:
            return RuleResult(True, RuleMatch("keyword", f"Ключевое слово: {keyword}"))
    return RuleResult(False)


def rule_link_overflow(message: Message, policy: Policy) -> RuleResult:
    if policy.max_links >= 0 and len(message.urls) > policy.max_links:
        return RuleResult(
            True,
            RuleMatch("link_overflow", f"Слишком много ссылок: {len(message.urls)}"),
        )
    return RuleResult(False)
