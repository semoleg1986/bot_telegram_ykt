from __future__ import annotations

import sqlite3
import time

from src.application import VpnIssuer
from src.infrastructure.clients.outline_client import OutlineClient
from src.infrastructure.vpn import XrayProfile

from .db import SQLiteDatabase

PROVIDER_OUTLINE = "outline"
PROVIDER_XRAY = "xray"


class SQLiteVpnIssuer(VpnIssuer):
    def __init__(
        self, db: SQLiteDatabase, ttl_days: int = 30, max_active: int = 2
    ) -> None:
        self._db = db
        self._db.ensure_schema()
        self._ttl_days = ttl_days
        self._max_active = max_active

    def _revoke_expired(self, conn: sqlite3.Connection) -> None:
        now = int(time.time())
        conn.execute(
            (
                "UPDATE vpn_keys SET revoked_at=? "
                "WHERE provider=? AND revoked_at IS NULL AND expires_at IS NOT NULL "
                "AND expires_at<=?"
            ),
            (now, PROVIDER_OUTLINE, now),
        )

    async def issue(self, user_id: int) -> str:
        conn = self._db.connect()
        try:
            self._revoke_expired(conn)
            now = int(time.time())
            row = conn.execute(
                """
                SELECT access_key FROM vpn_keys
                WHERE user_id=? AND provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                ORDER BY created_at DESC
                """,
                (user_id, PROVIDER_OUTLINE, now),
            ).fetchone()
            if row:
                return row["access_key"]
            active_count = conn.execute(
                """
                SELECT COUNT(*) as cnt FROM vpn_keys
                WHERE user_id=? AND provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                """,
                (user_id, PROVIDER_OUTLINE, now),
            ).fetchone()["cnt"]
            if active_count >= self._max_active:
                row = conn.execute(
                    """
                    SELECT access_key FROM vpn_keys
                    WHERE user_id=? AND provider=? AND revoked_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (user_id, PROVIDER_OUTLINE),
                ).fetchone()
                return row["access_key"]
            access_key = f"OUTLINE_ACCESS_KEY_FOR_{user_id}"
            expires_at = now + self._ttl_days * 86400
            conn.execute(
                """
                INSERT INTO vpn_keys(
                    user_id, access_key, provider, outline_key_id, created_at,
                    expires_at, revoked_at
                )
                VALUES(?, ?, ?, NULL, ?, ?, NULL)
                """,
                (user_id, access_key, PROVIDER_OUTLINE, now, expires_at),
            )
            conn.commit()
            return access_key
        finally:
            conn.close()

    async def revoke(self, user_id: int) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                "UPDATE vpn_keys SET revoked_at=? WHERE user_id=? AND provider=?",
                (int(time.time()), user_id, PROVIDER_OUTLINE),
            )
            conn.commit()
        finally:
            conn.close()

    async def stats(self) -> dict[str, int]:
        conn = self._db.connect()
        try:
            now = int(time.time())
            total = conn.execute(
                "SELECT COUNT(*) AS cnt FROM vpn_keys WHERE provider=?",
                (PROVIDER_OUTLINE,),
            ).fetchone()["cnt"]
            active = conn.execute(
                """
                SELECT COUNT(*) AS cnt FROM vpn_keys
                WHERE provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                """,
                (PROVIDER_OUTLINE, now),
            ).fetchone()["cnt"]
            revoked = conn.execute(
                """
                SELECT COUNT(*) AS cnt FROM vpn_keys
                WHERE provider=? AND revoked_at IS NOT NULL
                """,
                (PROVIDER_OUTLINE,),
            ).fetchone()["cnt"]
            return {"total": total, "active": active, "revoked": revoked}
        finally:
            conn.close()

    async def active_users(self, limit: int = 100) -> list[int]:
        conn = self._db.connect()
        try:
            now = int(time.time())
            rows = conn.execute(
                """
                SELECT DISTINCT user_id FROM vpn_keys
                WHERE provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                ORDER BY user_id ASC
                LIMIT ?
                """,
                (PROVIDER_OUTLINE, now, limit),
            ).fetchall()
            return [row["user_id"] for row in rows]
        finally:
            conn.close()


class XrayVpnIssuer(VpnIssuer):
    def __init__(
        self,
        db: SQLiteDatabase,
        profile: XrayProfile,
        ttl_days: int = 30,
        max_active: int = 2,
    ) -> None:
        self._db = db
        self._db.ensure_schema()
        self._profile = profile
        self._ttl_days = ttl_days
        self._max_active = max_active

    def _revoke_expired(self, conn: sqlite3.Connection) -> None:
        now = int(time.time())
        conn.execute(
            (
                "UPDATE vpn_keys SET revoked_at=? "
                "WHERE provider=? AND revoked_at IS NULL "
                "AND expires_at IS NOT NULL AND expires_at<=?"
            ),
            (now, PROVIDER_XRAY, now),
        )

    async def issue(self, user_id: int) -> str:
        conn = self._db.connect()
        try:
            self._revoke_expired(conn)
            now = int(time.time())
            row = conn.execute(
                """
                SELECT access_key FROM vpn_keys
                WHERE user_id=? AND provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                ORDER BY created_at DESC
                """,
                (user_id, PROVIDER_XRAY, now),
            ).fetchone()
            if row:
                return row["access_key"]

            active_count = conn.execute(
                """
                SELECT COUNT(*) as cnt FROM vpn_keys
                WHERE user_id=? AND provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                """,
                (user_id, PROVIDER_XRAY, now),
            ).fetchone()["cnt"]
            if active_count >= self._max_active:
                row = conn.execute(
                    """
                    SELECT access_key FROM vpn_keys
                    WHERE user_id=? AND provider=? AND revoked_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (user_id, PROVIDER_XRAY),
                ).fetchone()
                return row["access_key"]

            access_key = XrayProfile(
                host=self._profile.host,
                port=self._profile.port,
                uuid=self._profile.uuid,
                public_key=self._profile.public_key,
                sni=self._profile.sni,
                short_id=self._profile.short_id,
                name=f"{self._profile.name} {user_id}",
                flow=self._profile.flow,
                fingerprint=self._profile.fingerprint,
                alpn=self._profile.alpn,
                transport=self._profile.transport,
                security=self._profile.security,
                encryption=self._profile.encryption,
                path=self._profile.path,
            ).to_vless_url()
            expires_at = now + self._ttl_days * 86400
            conn.execute(
                """
                INSERT INTO vpn_keys(
                    user_id, access_key, provider, outline_key_id, created_at,
                    expires_at, revoked_at
                )
                VALUES(?, ?, ?, NULL, ?, ?, NULL)
                """,
                (user_id, access_key, PROVIDER_XRAY, now, expires_at),
            )
            conn.commit()
            return access_key
        finally:
            conn.close()

    async def revoke(self, user_id: int) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                "UPDATE vpn_keys SET revoked_at=? WHERE user_id=? AND provider=?",
                (int(time.time()), user_id, PROVIDER_XRAY),
            )
            conn.commit()
        finally:
            conn.close()

    async def stats(self) -> dict[str, int]:
        conn = self._db.connect()
        try:
            now = int(time.time())
            total = conn.execute(
                "SELECT COUNT(*) AS cnt FROM vpn_keys WHERE provider=?",
                (PROVIDER_XRAY,),
            ).fetchone()["cnt"]
            active = conn.execute(
                """
                SELECT COUNT(*) AS cnt FROM vpn_keys
                WHERE provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                """,
                (PROVIDER_XRAY, now),
            ).fetchone()["cnt"]
            revoked = conn.execute(
                """
                SELECT COUNT(*) AS cnt FROM vpn_keys
                WHERE provider=? AND revoked_at IS NOT NULL
                """,
                (PROVIDER_XRAY,),
            ).fetchone()["cnt"]
            return {"total": total, "active": active, "revoked": revoked}
        finally:
            conn.close()

    async def active_users(self, limit: int = 100) -> list[int]:
        conn = self._db.connect()
        try:
            now = int(time.time())
            rows = conn.execute(
                """
                SELECT DISTINCT user_id FROM vpn_keys
                WHERE provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                ORDER BY user_id ASC
                LIMIT ?
                """,
                (PROVIDER_XRAY, now, limit),
            ).fetchall()
            return [row["user_id"] for row in rows]
        finally:
            conn.close()


class OutlineVpnIssuer(VpnIssuer):
    def __init__(
        self,
        db: SQLiteDatabase,
        client: OutlineClient,
        ttl_days: int = 30,
        max_active: int = 2,
    ) -> None:
        self._db = db
        self._db.ensure_schema()
        self._client = client
        self._ttl_days = ttl_days
        self._max_active = max_active

    def _revoke_expired(self, conn: sqlite3.Connection) -> None:
        now = int(time.time())
        rows = conn.execute(
            """
            SELECT outline_key_id FROM vpn_keys
            WHERE provider=? AND revoked_at IS NULL AND expires_at IS NOT NULL
            AND expires_at<=?
            """,
            (PROVIDER_OUTLINE, now),
        ).fetchall()
        for row in rows:
            outline_key_id = row["outline_key_id"]
            if outline_key_id:
                self._client.delete_key(outline_key_id)
        conn.execute(
            (
                "UPDATE vpn_keys SET revoked_at=? "
                "WHERE provider=? AND revoked_at IS NULL "
                "AND expires_at IS NOT NULL "
                "AND expires_at<=?"
            ),
            (now, PROVIDER_OUTLINE, now),
        )

    async def issue(self, user_id: int) -> str:
        conn = self._db.connect()
        try:
            self._revoke_expired(conn)
            now = int(time.time())
            row = conn.execute(
                """
                SELECT access_key, outline_key_id FROM vpn_keys
                WHERE user_id=? AND provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                ORDER BY created_at DESC
                """,
                (user_id, PROVIDER_OUTLINE, now),
            ).fetchone()
            if row and row["access_key"]:
                return row["access_key"]

            active_count = conn.execute(
                """
                SELECT COUNT(*) as cnt FROM vpn_keys
                WHERE user_id=? AND provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                """,
                (user_id, PROVIDER_OUTLINE, now),
            ).fetchone()["cnt"]
            if active_count >= self._max_active:
                row = conn.execute(
                    """
                    SELECT access_key FROM vpn_keys
                    WHERE user_id=? AND provider=? AND revoked_at IS NULL
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (user_id, PROVIDER_OUTLINE),
                ).fetchone()
                return row["access_key"]

            response = self._client.create_key(name=str(user_id))
            access_key = response.get("accessUrl") or response.get("accessKey")
            outline_key_id = str(response.get("id"))
            if not access_key or outline_key_id == "None":
                raise RuntimeError("Outline API did not return access key")

            expires_at = now + self._ttl_days * 86400
            conn.execute(
                """
                INSERT INTO vpn_keys(
                    user_id, access_key, provider, outline_key_id, created_at,
                    expires_at, revoked_at
                )
                VALUES(?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    user_id,
                    access_key,
                    PROVIDER_OUTLINE,
                    outline_key_id,
                    now,
                    expires_at,
                ),
            )
            conn.commit()
            return access_key
        finally:
            conn.close()

    async def revoke(self, user_id: int) -> None:
        conn = self._db.connect()
        try:
            rows = conn.execute(
                """
                SELECT outline_key_id FROM vpn_keys
                WHERE user_id=? AND provider=? AND revoked_at IS NULL
                """,
                (user_id, PROVIDER_OUTLINE),
            ).fetchall()
            for row in rows:
                outline_key_id = row["outline_key_id"]
                if outline_key_id:
                    self._client.delete_key(outline_key_id)
            conn.execute(
                "UPDATE vpn_keys SET revoked_at=? WHERE user_id=? AND provider=?",
                (int(time.time()), user_id, PROVIDER_OUTLINE),
            )
            conn.commit()
        finally:
            conn.close()

    async def stats(self) -> dict[str, int]:
        conn = self._db.connect()
        try:
            now = int(time.time())
            total = conn.execute(
                "SELECT COUNT(*) AS cnt FROM vpn_keys WHERE provider=?",
                (PROVIDER_OUTLINE,),
            ).fetchone()["cnt"]
            active = conn.execute(
                """
                SELECT COUNT(*) AS cnt FROM vpn_keys
                WHERE provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                """,
                (PROVIDER_OUTLINE, now),
            ).fetchone()["cnt"]
            revoked = conn.execute(
                """
                SELECT COUNT(*) AS cnt FROM vpn_keys
                WHERE provider=? AND revoked_at IS NOT NULL
                """,
                (PROVIDER_OUTLINE,),
            ).fetchone()["cnt"]
            return {"total": total, "active": active, "revoked": revoked}
        finally:
            conn.close()

    async def active_users(self, limit: int = 100) -> list[int]:
        conn = self._db.connect()
        try:
            now = int(time.time())
            rows = conn.execute(
                """
                SELECT DISTINCT user_id FROM vpn_keys
                WHERE provider=? AND revoked_at IS NULL
                AND (expires_at IS NULL OR expires_at>?)
                ORDER BY user_id ASC
                LIMIT ?
                """,
                (PROVIDER_OUTLINE, now, limit),
            ).fetchall()
            return [row["user_id"] for row in rows]
        finally:
            conn.close()
