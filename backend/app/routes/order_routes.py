from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.order_service import create_order, mark_order_paid

router = APIRouter(prefix="/stores/{store_id}/orders", tags=["orders"])


@router.post("/")
async def create_store_order(store_id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    customer = payload.get("customer") or {}
    items = payload.get("items") or []
    if not items:
        raise HTTPException(status_code=400, detail="Order must contain items")
    order = await create_order(db, store_id, customer, items)
    return {"order_id": str(order.id), "total": float(order.total_amount)}


@router.post("/mark_paid")
async def mark_paid(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    order_id = payload.get("order_id")
    squad_ref = payload.get("squad_ref")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id required")
    order = await mark_order_paid(db, order_id, squad_ref)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return {"order_id": str(order.id), "status": order.order_status}
