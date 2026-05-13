from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.events import emit_event

router = APIRouter(prefix="/api", tags=["events"])


class EventRequest(BaseModel):
    event_type: str
    source: str
    user_id: str
    store_id: str | None = None
    order_id: str | None = None
    amount: float | None = None
    metadata: dict = {}
    timestamp: str | None = None
    idempotency_key: str | None = None


@router.post("/events")
async def ingest_event(payload: EventRequest, db: AsyncSession = Depends(get_db)):
    event = await emit_event(db, payload.dict(exclude_none=True))
    return {"id": str(event.id), "processed": event.processed, "event_type": event.event_type}
