from __future__ import annotations

from dataclasses import dataclass, field

from src.application import (
    ContextProvider,
    DecisionLogger,
    LogEntry,
    MessageAction,
    PolicyStore,
    VpnIssuer,
)
from src.domain import Policy


@dataclass
class InMemoryContextProvider(ContextProvider):
    texts_by_chat_user: dict[tuple[int, int], list[str]] = field(default_factory=dict)

    def add_text(self, chat_id: int, user_id: int, text: str) -> None:
        if not text:
            return
        key = (chat_id, user_id)
        self.texts_by_chat_user.setdefault(key, []).append(text)

    async def get_recent_texts(
        self, chat_id: int, user_id: int, window_sec: int
    ) -> tuple[str, ...]:
        _ = window_sec
        return tuple(self.texts_by_chat_user.get((chat_id, user_id), []))


@dataclass
class InMemoryDecisionLogger(DecisionLogger):
    entries: list[LogEntry] = field(default_factory=list)

    async def log(self, entry: LogEntry) -> None:
        self.entries.append(entry)


@dataclass
class InMemoryMessageAction(MessageAction):
    deleted: list[tuple[int, int]] = field(default_factory=list)
    notifications: list[tuple[int, str]] = field(default_factory=list)

    async def delete_message(self, chat_id: int, message_id: int) -> None:
        self.deleted.append((chat_id, message_id))

    async def notify_admins(self, chat_id: int, text: str) -> None:
        self.notifications.append((chat_id, text))


@dataclass
class InMemoryPolicyStore(PolicyStore):
    policy: Policy

    async def get(self) -> Policy:
        return self.policy

    async def update(self, updater) -> Policy:
        self.policy = updater(self.policy)
        return self.policy


@dataclass
class StubVpnIssuer(VpnIssuer):
    async def issue(self, user_id: int) -> str:
        return f"OUTLINE_ACCESS_KEY_FOR_{user_id}"

    async def revoke(self, user_id: int) -> None:
        _ = user_id
