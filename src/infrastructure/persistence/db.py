from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass


def split_csv(raw: str) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def join_csv(items: tuple[str, ...]) -> str:
    return ",".join(items)


@dataclass
class SQLiteDatabase:
    path: str

    def connect(self) -> sqlite3.Connection:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_schema(self) -> None:
        conn = self.connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS policy (
                    id INTEGER PRIMARY KEY,
                    keyword_list TEXT NOT NULL,
                    domain_blacklist TEXT NOT NULL,
                    domain_whitelist TEXT NOT NULL,
                    max_links INTEGER NOT NULL,
                    repeat_window_sec INTEGER NOT NULL,
                    repeat_threshold INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    is_spam INTEGER NOT NULL,
                    primary_reason TEXT NOT NULL,
                    matches_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS message_texts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                """
            )
            conn.commit()
        finally:
            conn.close()
