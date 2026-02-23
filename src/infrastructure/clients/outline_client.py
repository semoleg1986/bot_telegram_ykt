from __future__ import annotations

import hashlib
import json
import socket
import ssl
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse


@dataclass(frozen=True)
class OutlineClient:
    api_url: str
    cert_sha256: str | None = None

    def _verify_cert(self) -> None:
        if not self.cert_sha256:
            return
        parsed = urlparse(self.api_url)
        host = parsed.hostname
        if not host:
            raise ValueError("Invalid OUTLINE_API_URL")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with context.wrap_socket(socket.socket(), server_hostname=host) as sock:
            sock.settimeout(10)
            sock.connect((host, port))
            cert = sock.getpeercert(binary_form=True)
        fingerprint = hashlib.sha256(cert).hexdigest().upper()
        expected = self.cert_sha256.replace(":", "").upper()
        if fingerprint != expected:
            raise RuntimeError("Outline cert fingerprint mismatch")

    def _request(self, method: str, path: str, payload: dict | None = None) -> Any:
        self._verify_cert()
        url = urljoin(self.api_url.rstrip("/") + "/", path.lstrip("/"))
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context, timeout=10) as resp:
            body = resp.read().decode("utf-8")
        if not body:
            return None
        return json.loads(body)

    def create_key(self, name: str | None = None) -> dict:
        payload = {"name": name} if name else {}
        return self._request("POST", "/access-keys", payload)

    def list_keys(self) -> dict:
        return self._request("GET", "/access-keys")

    def delete_key(self, key_id: str) -> None:
        self._request("DELETE", f"/access-keys/{key_id}")
