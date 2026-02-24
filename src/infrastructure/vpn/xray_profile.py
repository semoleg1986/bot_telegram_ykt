from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, urlencode


@dataclass(frozen=True)
class XrayProfile:
    host: str
    port: int
    uuid: str
    public_key: str
    sni: str
    short_id: str
    name: str = "VPN"
    flow: str = "xtls-rprx-vision"
    fingerprint: str = "chrome"
    alpn: str = "h2"
    transport: str = "tcp"
    security: str = "reality"
    encryption: str = "none"
    path: str = "/"

    def to_vless_url(self) -> str:
        params = {
            "type": self.transport,
            "security": self.security,
            "encryption": self.encryption,
            "flow": self.flow,
            "sni": self.sni,
            "fp": self.fingerprint,
            "alpn": self.alpn,
            "pbk": self.public_key,
            "sid": self.short_id,
        }
        if self.path:
            params["spx"] = self.path
        query = urlencode(params, safe="/")
        fragment = quote(self.name, safe="")
        return f"vless://{self.uuid}@{self.host}:{self.port}" f"?{query}#{fragment}"
