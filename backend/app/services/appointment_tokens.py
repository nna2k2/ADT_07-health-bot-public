from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii"))


def sign_token(payload: dict, *, secret: str, ttl_seconds: int = 60 * 60 * 24 * 7) -> str:
    now = int(time.time())
    body = dict(payload)
    body["iat"] = now
    body["exp"] = now + int(ttl_seconds)
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    msg = _b64url_encode(raw)
    sig = hmac.new(secret.encode("utf-8"), msg.encode("ascii"), hashlib.sha256).digest()
    return f"{msg}.{_b64url_encode(sig)}"


def verify_token(token: str, *, secret: str) -> dict:
    try:
        msg, sig = token.split(".", 1)
    except ValueError as e:
        raise ValueError("bad_token_format") from e

    expected = hmac.new(secret.encode("utf-8"), msg.encode("ascii"), hashlib.sha256).digest()
    got = _b64url_decode(sig)
    if not hmac.compare_digest(expected, got):
        raise ValueError("bad_signature")

    body = json.loads(_b64url_decode(msg).decode("utf-8"))
    exp = int(body.get("exp", 0) or 0)
    if exp and int(time.time()) > exp:
        raise ValueError("expired")
    return body

