"""
Session and rate-limit storage.

Uses Upstash Redis when configured. In local development, where the Upstash URL
and token are often blank, it falls back to a small in-memory store so webhook
handling does not crash before the actual WhatsApp logic runs.
"""
import json
import time

from upstash_redis.asyncio import Redis

from app.config import settings


USE_UPSTASH = bool(settings.upstash_redis_rest_url and settings.upstash_redis_rest_token)
redis = (
    Redis(url=settings.upstash_redis_rest_url, token=settings.upstash_redis_rest_token)
    if USE_UPSTASH
    else None
)

_memory_store: dict[str, tuple[object, float | None]] = {}


def _default_session() -> dict:
    return {
        "stage": "NEW",
        "agent": None,
        "language": None,
        "pending_data": {},
        "awaiting_pin": False,
        "pin_action": None,
        "step": 0,
        "onboarding_complete": False,
        "pin_attempts": 0,
    }


def _memory_get(key: str):
    row = _memory_store.get(key)
    if not row:
        return None
    value, expires_at = row
    if expires_at is not None and expires_at <= time.time():
        _memory_store.pop(key, None)
        return None
    return value


def _memory_setex(key: str, ttl_seconds: int, value):
    _memory_store[key] = (value, time.time() + ttl_seconds)


def _memory_delete(key: str):
    _memory_store.pop(key, None)


def _loads(value):
    return json.loads(value) if isinstance(value, str) else value


async def _get(key: str):
    if USE_UPSTASH:
        return await redis.get(key)
    return _memory_get(key)


async def _setex(key: str, ttl_seconds: int, value):
    if USE_UPSTASH:
        await redis.setex(key, ttl_seconds, value)
        return
    _memory_setex(key, ttl_seconds, value)


async def _delete(key: str):
    if USE_UPSTASH:
        await redis.delete(key)
        return
    _memory_delete(key)


async def _incr(key: str) -> int:
    if USE_UPSTASH:
        return await redis.incr(key)
    count = int(_memory_get(key) or 0) + 1
    existing = _memory_store.get(key)
    expires_at = existing[1] if existing else None
    _memory_store[key] = (count, expires_at)
    return count


async def _expire(key: str, ttl_seconds: int):
    if USE_UPSTASH:
        await redis.expire(key, ttl_seconds)
        return
    value = _memory_get(key)
    if value is not None:
        _memory_setex(key, ttl_seconds, value)


async def get_session(whatsapp_no: str) -> dict:
    data = await _get(f"session:{whatsapp_no}")
    return _loads(data) if data else _default_session()


async def save_session(whatsapp_no: str, data: dict):
    await _setex(f"session:{whatsapp_no}", 1800, json.dumps(data))


async def clear_session(whatsapp_no: str):
    await _delete(f"session:{whatsapp_no}")


async def save_flow_session(token: str, data: dict):
    await _setex(f"flow_session:{token}", 1800, json.dumps(data))


async def get_flow_session(token: str) -> dict | None:
    data = await _get(f"flow_session:{token}")
    return _loads(data) if data else None


async def clear_flow_session(token: str):
    await _delete(f"flow_session:{token}")


async def increment_pin_attempts(whatsapp_no: str) -> int:
    key = f"pin_attempts:{whatsapp_no}"
    attempts = await _incr(key)
    if attempts == 1:
        await _expire(key, 600)
    return attempts


async def clear_pin_attempts(whatsapp_no: str):
    await _delete(f"pin_attempts:{whatsapp_no}")


async def set_mono_pending(whatsapp_no: str):
    await _setex(f"mono_pending:{whatsapp_no}", 1800, "1")


async def clear_mono_pending(whatsapp_no: str):
    await _delete(f"mono_pending:{whatsapp_no}")


async def is_mono_pending(whatsapp_no: str) -> bool:
    return await _get(f"mono_pending:{whatsapp_no}") is not None


async def set_rate_limit(whatsapp_no: str) -> int:
    key = f"rate_limit:{whatsapp_no}"
    count = await _incr(key)
    if count == 1:
        await _expire(key, 60)
    return count


MAX_HISTORY_DEPTH = 10
_HISTORY_TTL = 1800


async def push_state_history(whatsapp_no: str, session: dict) -> None:
    key = f"state_history:{whatsapp_no}"
    raw = await _get(key)
    history: list = _loads(raw) if raw else []
    history.append(session)
    if len(history) > MAX_HISTORY_DEPTH:
        history = history[-MAX_HISTORY_DEPTH:]
    await _setex(key, _HISTORY_TTL, json.dumps(history))


async def pop_state_history(whatsapp_no: str) -> dict | None:
    key = f"state_history:{whatsapp_no}"
    raw = await _get(key)
    if not raw:
        return None
    history: list = _loads(raw)
    if not history:
        return None
    previous_session: dict = history.pop()
    await _setex(key, _HISTORY_TTL, json.dumps(history))
    await save_session(whatsapp_no, previous_session)
    return previous_session


async def clear_state_history(whatsapp_no: str) -> None:
    await _delete(f"state_history:{whatsapp_no}")
