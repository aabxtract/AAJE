import logging
from typing import Any, Dict

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_event(event: Dict[str, Any]) -> bool:
    """Send event to Squad Intelligence endpoint.

    Uses `settings.squad_base_url` as the base and posts to `/intelligence/events`.
    In production this should use authenticated client and retry/backoff.
    """
    url = f"{settings.squad_base_url.rstrip('/')}/intelligence/events"
    headers = {"Content-Type": "application/json"}
    # If there's a secret key available, send as Authorization header
    if getattr(settings, "squad_secret_key", None):
        headers["Authorization"] = f"Bearer {settings.squad_secret_key}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=event, headers=headers)
            resp.raise_for_status()
        logger.info("Sent intelligence event to %s", url)
        return True
    except Exception as exc:
        logger.exception("Failed to send intelligence event: %s", exc)
        return False
