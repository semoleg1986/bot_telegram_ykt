from __future__ import annotations

import json
import time
from typing import Any

from .db import SQLiteDatabase


class SQLiteCache:
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db
        self._db.ensure_schema()

    def get(self, key: str, ttl_sec: int) -> dict[str, Any] | None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                "SELECT value_json, updated_at FROM cache WHERE key=?",
                (key,),
            ).fetchone()
            if not row:
                return None
            updated_at = int(row["updated_at"])
            if int(time.time()) - updated_at > ttl_sec:
                return None
            return json.loads(row["value_json"])
        finally:
            conn.close()

    def set(self, key: str, value: dict[str, Any]) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                """
                INSERT INTO cache(key, value_json, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json=excluded.value_json,
                    updated_at=excluded.updated_at
                """,
                (key, json.dumps(value), int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()
