from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from src.domain import Policy, SpamDecision


@dataclass(frozen=True)
class LogEntry:
    chat_id: int
    message_id: int
    user_id: int
    decision: SpamDecision
    policy: Policy


class ContextProvider(Protocol):
    async def get_recent_texts(
        self, chat_id: int, user_id: int, window_sec: int
    ) -> tuple[str, ...]:
        raise NotImplementedError


class DecisionLogger(Protocol):
    async def log(self, entry: LogEntry) -> None:
        raise NotImplementedError


class MessageAction(Protocol):
    async def delete_message(self, chat_id: int, message_id: int) -> None:
        raise NotImplementedError

    async def notify_admins(self, chat_id: int, text: str) -> None:
        raise NotImplementedError


class PolicyStore(Protocol):
    async def get(self) -> Policy:
        raise NotImplementedError

    async def update(self, updater: Callable[[Policy], Policy]) -> Policy:
        raise NotImplementedError


class VpnIssuer(Protocol):
    async def issue(self, user_id: int) -> str:
        raise NotImplementedError

    async def revoke(self, user_id: int) -> None:
        raise NotImplementedError
