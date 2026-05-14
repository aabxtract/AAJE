import logging
from typing import Any, Dict

from app.services.intelligence_client import send_event

logger = logging.getLogger(__name__)


async def emit_event(session, event: Dict[str, Any]):
    """Emit intelligence event.

    Currently posts directly to the Squad Intelligence endpoint via `intelligence_client`.
    In the future this can be extended to queue events, batch, or retry on failure.
    """
    # enrich/normalize event here if needed
    ok = await send_event(event)
    if not ok:
        logger.warning("Intelligence event failed to send; consider retrying: %s", event)
    else:
        logger.info("Intelligence event emitted: %s", event)
