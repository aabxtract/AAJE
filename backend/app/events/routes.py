from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.events.handlers import emit_event
from app.models.intelligence import Event
from sqlalchemy import select

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


@router.get("/events/store/{store_id}")
async def list_events_for_store(store_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Event).where(Event.store_id == store_id).order_by(Event.created_at.desc()))).scalars().all()
    return [{"id": str(r.id), "event_type": r.event_type, "payload": r.payload_json, "processed": r.processed, "created_at": r.created_at.isoformat()} for r in rows]
