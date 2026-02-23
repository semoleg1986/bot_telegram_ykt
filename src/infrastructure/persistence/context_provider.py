from __future__ import annotations

import time

from src.application import ContextProvider

from .db import SQLiteDatabase


class SQLiteContextProvider(ContextProvider):
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db
        self._db.ensure_schema()

    def add_text(self, chat_id: int, user_id: int, text: str) -> None:
        if not text:
            return
        conn = self._db.connect()
        try:
            conn.execute(
                """
                INSERT INTO message_texts(created_at, chat_id, user_id, text)
                VALUES(?, ?, ?, ?)
                """,
                (int(time.time()), chat_id, user_id, text),
            )
            conn.commit()
        finally:
            conn.close()

    async def get_recent_texts(
        self, chat_id: int, user_id: int, window_sec: int
    ) -> tuple[str, ...]:
        conn = self._db.connect()
        try:
            cutoff = int(time.time()) - window_sec
            rows = conn.execute(
                """
                SELECT text FROM message_texts
                WHERE chat_id=? AND user_id=? AND created_at>=?
                ORDER BY id DESC
                """,
                (chat_id, user_id, cutoff),
            ).fetchall()
            return tuple(row["text"] for row in rows)
        finally:
            conn.close()
