from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RuleMatch:
    code: str
    reason: str


@dataclass(frozen=True)
class SpamDecision:
    is_spam: bool
    matches: tuple[RuleMatch, ...] = field(default_factory=tuple)

    @property
    def primary_reason(self) -> str:
        if not self.matches:
            return ""
        return self.matches[0].reason
