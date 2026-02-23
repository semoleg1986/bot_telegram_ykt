from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .decision import RuleMatch, SpamDecision
from .models import Message, User
from .policy import Policy
from .rules import (
    rule_blocklisted_domain,
    rule_keyword_match,
    rule_link_overflow,
    rule_whitelisted_domain,
)


@dataclass(frozen=True)
class SpamContext:
    recent_texts: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_texts(cls, texts: Iterable[str]) -> "SpamContext":
        return cls(recent_texts=tuple(t for t in texts if t))


def _rule_repeat(
    message: Message, policy: Policy, context: SpamContext
) -> RuleMatch | None:
    if policy.repeat_threshold <= 0:
        return None
    normalized = message.text.strip().lower()
    if not normalized:
        return None
    repeats = sum(1 for t in context.recent_texts if t.strip().lower() == normalized)
    if repeats >= policy.repeat_threshold:
        return RuleMatch("repeat", f"Повтор сообщения: {repeats + 1} раз(а)")
    return None


def evaluate_message(
    message: Message, user: User, policy: Policy, context: SpamContext
) -> SpamDecision:
    if user.is_admin or user.is_whitelisted:
        return SpamDecision(is_spam=False)

    normalized_policy = policy.normalized()
    matches: list[RuleMatch] = []

    whitelist_match = rule_whitelisted_domain(message, normalized_policy)
    if whitelist_match.matched:
        return SpamDecision(
            is_spam=False,
            matches=(whitelist_match.match,) if whitelist_match.match else (),
        )

    for rule_fn in (rule_blocklisted_domain, rule_keyword_match, rule_link_overflow):
        result = rule_fn(message, normalized_policy)
        if result.matched and result.match:
            matches.append(result.match)

    repeat_match = _rule_repeat(message, normalized_policy, context)
    if repeat_match:
        matches.append(repeat_match)

    return SpamDecision(is_spam=bool(matches), matches=tuple(matches))
