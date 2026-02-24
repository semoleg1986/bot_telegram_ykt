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

                CREATE TABLE IF NOT EXISTS vpn_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    access_key TEXT NOT NULL,
                    outline_key_id TEXT,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER,
                    revoked_at INTEGER
                );

                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                """
            )
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(vpn_keys)").fetchall()
            }
            if "id" not in columns:
                conn.execute("DROP TABLE IF EXISTS vpn_keys_new")
                conn.execute(
                    """
                    CREATE TABLE vpn_keys_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        access_key TEXT NOT NULL,
                        outline_key_id TEXT,
                        created_at INTEGER NOT NULL,
                        expires_at INTEGER,
                        revoked_at INTEGER
                    )
                    """
                )
                if "outline_key_id" not in columns:
                    conn.execute(
                        """
                        INSERT INTO vpn_keys_new(
                            user_id, access_key, created_at, revoked_at
                        )
                        SELECT user_id, access_key, created_at, revoked_at
                        FROM vpn_keys
                        """
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO vpn_keys_new(
                            user_id, access_key, outline_key_id, created_at, revoked_at
                        )
                        SELECT user_id, access_key, outline_key_id, created_at,
                               revoked_at
                        FROM vpn_keys
                        """
                    )
                conn.execute("DROP TABLE vpn_keys")
                conn.execute("ALTER TABLE vpn_keys_new RENAME TO vpn_keys")
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(vpn_keys)").fetchall()
            }
            if "outline_key_id" not in columns:
                conn.execute("ALTER TABLE vpn_keys ADD COLUMN outline_key_id TEXT")
            if "expires_at" not in columns:
                conn.execute("ALTER TABLE vpn_keys ADD COLUMN expires_at INTEGER")
            conn.commit()
        finally:
            conn.close()
