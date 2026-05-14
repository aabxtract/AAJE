from datetime import datetime, timezone
from typing import Any

from app.services.intelligence_sync import emit_event as emit_intelligence_event


async def emit_storefront_event(session, event_type: str, **payload: Any) -> None:
    event = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **{key: value for key, value in payload.items() if value is not None},
    }
    await emit_intelligence_event(session, event)
