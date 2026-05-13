"""
Upstash Redis client — uses the upstash-redis SDK with async support.
All keys are namespaced and TTL-managed so expired sessions self-delete.

State history stack
-------------------
Every time the onboarding agent is about to advance to a new stage it calls
``push_state_history(whatsapp_no, session)`` to snapshot the *current* state.
The user can then send "back", "undo", or "go back" and the session router
calls ``pop_state_history(whatsapp_no)`` to restore the previous snapshot.
The stack is capped at MAX_HISTORY_DEPTH entries and expires with the session.
"""
import json
from upstash_redis.asyncio import Redis
from app.config import settings

redis = Redis(
    url=settings.upstash_redis_rest_url,
    token=settings.upstash_redis_rest_token,
)


async def get_session(whatsapp_no: str) -> dict:
    """Get session from Redis. Returns default new session if not found."""
    data = await redis.get(f"session:{whatsapp_no}")
    if data:
        return json.loads(data) if isinstance(data, str) else data
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


async def save_session(whatsapp_no: str, data: dict):
    """Save session with 30-minute TTL."""
    await redis.setex(
        f"session:{whatsapp_no}",
        1800,
        json.dumps(data),
    )


async def clear_session(whatsapp_no: str):
    await redis.delete(f"session:{whatsapp_no}")


async def save_flow_session(token: str, data: dict):
    """Save browser Flow session metadata with 30-minute TTL."""
    await redis.setex(
        f"flow_session:{token}",
        1800,
        json.dumps(data),
    )


async def get_flow_session(token: str) -> dict | None:
    data = await redis.get(f"flow_session:{token}")
    if not data:
        return None
    return json.loads(data) if isinstance(data, str) else data


async def clear_flow_session(token: str):
    await redis.delete(f"flow_session:{token}")


async def increment_pin_attempts(whatsapp_no: str) -> int:
    """Increment PIN attempt counter. 10-minute TTL window."""
    key = f"pin_attempts:{whatsapp_no}"
    attempts = await redis.incr(key)
    if attempts == 1:
        await redis.expire(key, 600)
    return attempts


async def clear_pin_attempts(whatsapp_no: str):
    await redis.delete(f"pin_attempts:{whatsapp_no}")


async def set_mono_pending(whatsapp_no: str):
    """Flag that this trader is in the Mono Connect flow."""
    await redis.setex(f"mono_pending:{whatsapp_no}", 1800, "1")


async def clear_mono_pending(whatsapp_no: str):
    await redis.delete(f"mono_pending:{whatsapp_no}")


async def is_mono_pending(whatsapp_no: str) -> bool:
    result = await redis.get(f"mono_pending:{whatsapp_no}")
    return result is not None


async def set_rate_limit(whatsapp_no: str) -> int:
    """Rate limit counter. 60-second window. Returns current count."""
    key = f"rate_limit:{whatsapp_no}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    return count


# ── State history (revert / back action) ──────────────────────────────────────

MAX_HISTORY_DEPTH = 10
_HISTORY_TTL = 1800  # match session TTL (30 min)


async def push_state_history(whatsapp_no: str, session: dict) -> None:
    """
    Snapshot *current* session before a stage transition.

    Call this BEFORE overwriting ``session["stage"]`` so the snapshot
    captures the state the user is about to leave.
    """
    key = f"state_history:{whatsapp_no}"
    # Fetch existing history (stored as a JSON list)
    raw = await redis.get(key)
    history: list = json.loads(raw) if raw else []

    # Only keep the last MAX_HISTORY_DEPTH entries
    history.append(session)
    if len(history) > MAX_HISTORY_DEPTH:
        history = history[-MAX_HISTORY_DEPTH:]

    await redis.setex(key, _HISTORY_TTL, json.dumps(history))


async def pop_state_history(whatsapp_no: str) -> dict | None:
    """
    Restore the most-recent snapshot.

    Returns the restored session dict (already saved back to Redis) or
    ``None`` if there is no history to go back to.
    """
    key = f"state_history:{whatsapp_no}"
    raw = await redis.get(key)
    if not raw:
        return None

    history: list = json.loads(raw) if isinstance(raw, str) else raw
    if not history:
        return None

    # Pop the last snapshot
    previous_session: dict = history.pop()

    # Persist the updated (shorter) history stack
    await redis.setex(key, _HISTORY_TTL, json.dumps(history))

    # Restore the session in Redis so the next message handler sees it
    await save_session(whatsapp_no, previous_session)
    return previous_session


async def clear_state_history(whatsapp_no: str) -> None:
    """Wipe the history stack — called on full session reset or onboarding completion."""
    await redis.delete(f"state_history:{whatsapp_no}")
