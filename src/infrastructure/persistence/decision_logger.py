from __future__ import annotations

import json
import time

from src.application import DecisionLogger, LogEntry

from .db import SQLiteDatabase


class SQLiteDecisionLogger(DecisionLogger):
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db
        self._db.ensure_schema()

    async def log(self, entry: LogEntry) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                """
                INSERT INTO decisions(
                    created_at, chat_id, message_id, user_id,
                    is_spam, primary_reason, matches_json
                )
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(time.time()),
                    entry.chat_id,
                    entry.message_id,
                    entry.user_id,
                    1 if entry.decision.is_spam else 0,
                    entry.decision.primary_reason or "",
                    json.dumps([m.__dict__ for m in entry.decision.matches]),
                ),
            )
            conn.commit()
        finally:
            conn.close()
