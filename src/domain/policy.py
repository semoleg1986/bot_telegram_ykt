from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Policy:
    keyword_list: tuple[str, ...] = field(default_factory=tuple)
    domain_blacklist: tuple[str, ...] = field(default_factory=tuple)
    domain_whitelist: tuple[str, ...] = field(default_factory=tuple)
    max_links: int = 2
    repeat_window_sec: int = 300
    repeat_threshold: int = 2

    def normalized(self) -> "Policy":
        return Policy(
            keyword_list=tuple(k.lower() for k in self.keyword_list),
            domain_blacklist=tuple(d.lower() for d in self.domain_blacklist),
            domain_whitelist=tuple(d.lower() for d in self.domain_whitelist),
            max_links=self.max_links,
            repeat_window_sec=self.repeat_window_sec,
            repeat_threshold=self.repeat_threshold,
        )
