"""
Upstash Redis client — uses the upstash-redis SDK with async support.
All keys are namespaced and TTL-managed so expired sessions self-delete.
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
