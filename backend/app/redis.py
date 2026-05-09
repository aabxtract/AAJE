"""
Upstash Redis client — REST-based, no persistent TCP connection needed.
All keys are namespaced and TTL-managed so expired sessions self-delete.
"""
import json
from typing import Any

import httpx

from app.config import settings

# TTL constants (seconds)
SESSION_TTL = 1800       # 30 min
PIN_ATTEMPTS_TTL = 600   # 10 min
MONO_PENDING_TTL = 1800  # 30 min
RATE_LIMIT_TTL = 60      # 60 sec

_HEADERS = {
    "Authorization": f"Bearer {settings.UPSTASH_REDIS_REST_TOKEN}",
    "Content-Type": "application/json",
}
_BASE = settings.UPSTASH_REDIS_REST_URL.rstrip("/")


async def _request(command: list) -> Any:
    """Send a raw Redis command to Upstash REST endpoint."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{_BASE}", headers=_HEADERS, json=command)
        resp.raise_for_status()
        return resp.json().get("result")


# ── Key builders ────────────────────────────────────────────────────────────

def session_key(wa_no: str) -> str:
    return f"session:{wa_no}"

def pin_attempts_key(wa_no: str) -> str:
    return f"pin_attempts:{wa_no}"

def mono_pending_key(wa_no: str) -> str:
    return f"mono_pending:{wa_no}"

def rate_limit_key(wa_no: str) -> str:
    return f"rate_limit:{wa_no}"


# ── Generic helpers ──────────────────────────────────────────────────────────

async def get_json(key: str) -> dict | None:
    raw = await _request(["GET", key])
    return json.loads(raw) if raw else None


async def set_json(key: str, value: dict, ttl: int) -> None:
    await _request(["SET", key, json.dumps(value), "EX", ttl])


async def delete(key: str) -> None:
    await _request(["DEL", key])


async def increment(key: str, ttl: int) -> int:
    count = await _request(["INCR", key])
    if count == 1:
        await _request(["EXPIRE", key, ttl])
    return count
