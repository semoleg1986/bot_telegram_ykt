from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Callable

from src.application import (
    ContextProvider,
    DecisionLogger,
    LogEntry,
    PolicyStore,
    VpnIssuer,
)
from src.domain import Policy
from src.infrastructure.outline_client import OutlineClient


def _split_csv(raw: str) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _join_csv(items: tuple[str, ...]) -> str:
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
                    user_id INTEGER PRIMARY KEY,
                    access_key TEXT NOT NULL,
                    outline_key_id TEXT,
                    created_at INTEGER NOT NULL,
                    revoked_at INTEGER
                );
                """
            )
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(vpn_keys)").fetchall()
            }
            if "outline_key_id" not in columns:
                conn.execute("ALTER TABLE vpn_keys ADD COLUMN outline_key_id TEXT")
            conn.commit()
        finally:
            conn.close()


class SQLitePolicyStore(PolicyStore):
    def __init__(self, db: SQLiteDatabase, initial_policy: Policy) -> None:
        self._db = db
        self._db.ensure_schema()
        self._ensure_initial(initial_policy.normalized())

    def _ensure_initial(self, policy: Policy) -> None:
        conn = self._db.connect()
        try:
            row = conn.execute("SELECT id FROM policy WHERE id=1").fetchone()
            if row:
                return
            conn.execute(
                """
                INSERT INTO policy(
                    id, keyword_list, domain_blacklist, domain_whitelist,
                    max_links, repeat_window_sec, repeat_threshold
                )
                VALUES(1, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _join_csv(policy.keyword_list),
                    _join_csv(policy.domain_blacklist),
                    _join_csv(policy.domain_whitelist),
                    policy.max_links,
                    policy.repeat_window_sec,
                    policy.repeat_threshold,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    async def get(self) -> Policy:
        conn = self._db.connect()
        try:
            row = conn.execute("SELECT * FROM policy WHERE id=1").fetchone()
            if not row:
                return Policy()
            return Policy(
                keyword_list=_split_csv(row["keyword_list"]),
                domain_blacklist=_split_csv(row["domain_blacklist"]),
                domain_whitelist=_split_csv(row["domain_whitelist"]),
                max_links=row["max_links"],
                repeat_window_sec=row["repeat_window_sec"],
                repeat_threshold=row["repeat_threshold"],
            ).normalized()
        finally:
            conn.close()

    async def update(self, updater: Callable[[Policy], Policy]) -> Policy:
        current = await self.get()
        updated = updater(current).normalized()
        conn = self._db.connect()
        try:
            conn.execute(
                """
                UPDATE policy
                SET keyword_list=?, domain_blacklist=?, domain_whitelist=?,
                    max_links=?, repeat_window_sec=?, repeat_threshold=?
                WHERE id=1
                """,
                (
                    _join_csv(updated.keyword_list),
                    _join_csv(updated.domain_blacklist),
                    _join_csv(updated.domain_whitelist),
                    updated.max_links,
                    updated.repeat_window_sec,
                    updated.repeat_threshold,
                ),
            )
            conn.commit()
            return updated
        finally:
            conn.close()


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


class SQLiteVpnIssuer(VpnIssuer):
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db
        self._db.ensure_schema()

    async def issue(self, user_id: int) -> str:
        conn = self._db.connect()
        try:
            row = conn.execute(
                """
                SELECT access_key FROM vpn_keys
                WHERE user_id=? AND revoked_at IS NULL
                """,
                (user_id,),
            ).fetchone()
            if row:
                return row["access_key"]
            access_key = f"OUTLINE_ACCESS_KEY_FOR_{user_id}"
            conn.execute(
                """
                INSERT INTO vpn_keys(
                    user_id, access_key, outline_key_id, created_at, revoked_at
                )
                VALUES(?, ?, NULL, ?, NULL)
                """,
                (user_id, access_key, int(time.time())),
            )
            conn.commit()
            return access_key
        finally:
            conn.close()

    async def revoke(self, user_id: int) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                "UPDATE vpn_keys SET revoked_at=? WHERE user_id=?",
                (int(time.time()), user_id),
            )
            conn.commit()
        finally:
            conn.close()


class OutlineVpnIssuer(VpnIssuer):
    def __init__(self, db: SQLiteDatabase, client: OutlineClient) -> None:
        self._db = db
        self._db.ensure_schema()
        self._client = client

    async def issue(self, user_id: int) -> str:
        conn = self._db.connect()
        try:
            row = conn.execute(
                """
                SELECT access_key, outline_key_id FROM vpn_keys
                WHERE user_id=? AND revoked_at IS NULL
                """,
                (user_id,),
            ).fetchone()
            if row and row["access_key"]:
                return row["access_key"]

            response = self._client.create_key(name=str(user_id))
            access_key = response.get("accessUrl") or response.get("accessKey")
            outline_key_id = str(response.get("id"))
            if not access_key or outline_key_id == "None":
                raise RuntimeError("Outline API did not return access key")

            conn.execute(
                """
                INSERT INTO vpn_keys(
                    user_id, access_key, outline_key_id, created_at, revoked_at
                )
                VALUES(?, ?, ?, ?, NULL)
                """,
                (user_id, access_key, outline_key_id, int(time.time())),
            )
            conn.commit()
            return access_key
        finally:
            conn.close()

    async def revoke(self, user_id: int) -> None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                """
                SELECT outline_key_id FROM vpn_keys
                WHERE user_id=? AND revoked_at IS NULL
                """,
                (user_id,),
            ).fetchone()
            outline_key_id = row["outline_key_id"] if row else None
            if outline_key_id:
                self._client.delete_key(outline_key_id)
            conn.execute(
                "UPDATE vpn_keys SET revoked_at=? WHERE user_id=?",
                (int(time.time()), user_id),
            )
            conn.commit()
        finally:
            conn.close()
