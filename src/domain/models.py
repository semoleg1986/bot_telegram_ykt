from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class User:
    user_id: int
    is_admin: bool = False
    is_whitelisted: bool = False


@dataclass(frozen=True)
class Message:
    message_id: int
    chat_id: int
    user_id: int
    text: str = ""
    urls: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_text(
        cls, message_id: int, chat_id: int, user_id: int, text: str
    ) -> "Message":
        return cls(
            message_id=message_id, chat_id=chat_id, user_id=user_id, text=text or ""
        )

    def with_urls(self, urls: Iterable[str]) -> "Message":
        return Message(
            message_id=self.message_id,
            chat_id=self.chat_id,
            user_id=self.user_id,
            text=self.text,
            urls=tuple(urls),
        )
