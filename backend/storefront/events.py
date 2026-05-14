from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .sync import emit_storefront_event

router = APIRouter()


class StorefrontEventPayload(BaseModel):
    event_type: str
    user_id: str | None = None
    store_id: str | None = None
    order_id: str | None = None
    product_id: str | None = None
    product_name: str | None = None
    category: str | None = None
    quantity: int | None = None
    amount: float | None = None
    timestamp: str | None = None
    metadata: dict[str, Any] | None = None


@router.post("/storefront")
async def storefront_event(payload: StorefrontEventPayload, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump()
    event_type = data.pop("event_type")
    await emit_storefront_event(db, event_type, **data)
    return {"ok": True}
