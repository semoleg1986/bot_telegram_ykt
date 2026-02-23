from __future__ import annotations

from typing import Callable

from src.application import PolicyStore
from src.domain import Policy

from .db import SQLiteDatabase, join_csv, split_csv


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
                    join_csv(policy.keyword_list),
                    join_csv(policy.domain_blacklist),
                    join_csv(policy.domain_whitelist),
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
                keyword_list=split_csv(row["keyword_list"]),
                domain_blacklist=split_csv(row["domain_blacklist"]),
                domain_whitelist=split_csv(row["domain_whitelist"]),
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
                    join_csv(updated.keyword_list),
                    join_csv(updated.domain_blacklist),
                    join_csv(updated.domain_whitelist),
                    updated.max_links,
                    updated.repeat_window_sec,
                    updated.repeat_threshold,
                ),
            )
            conn.commit()
            return updated
        finally:
            conn.close()
