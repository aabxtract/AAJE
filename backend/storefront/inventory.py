import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import InventoryMovement, Product, Store
from .sync import emit_storefront_event

router = APIRouter()


class InventoryAdjustPayload(BaseModel):
    store_id: str
    product_id: str
    movement_type: str
    quantity: int
    reason: str | None = None
    related_order_id: str | None = None


def serialize_movement(movement: InventoryMovement, product: Product | None = None) -> dict[str, Any]:
    return {
        "id": str(movement.id),
        "store_id": str(movement.store_id),
        "product_id": str(movement.product_id),
        "product_name": product.name if product else None,
        "movement_type": movement.movement_type,
        "quantity": movement.quantity,
        "reason": movement.reason,
        "related_order_id": str(movement.related_order_id) if movement.related_order_id else None,
        "created_at": movement.created_at.isoformat() if movement.created_at else None,
    }


async def adjust_product_stock(db: AsyncSession, payload: InventoryAdjustPayload) -> tuple[Product, InventoryMovement]:
    product = await db.get(Product, uuid.UUID(payload.product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    quantity = abs(payload.quantity)
    if payload.movement_type == "stock_added":
        product.stock_quantity += quantity
    elif payload.movement_type in {"stock_removed", "order_paid", "order_cancelled"}:
        if product.stock_quantity - quantity < 0:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        product.stock_quantity -= quantity
    elif payload.movement_type == "manual_adjustment":
        product.stock_quantity = quantity
    else:
        raise HTTPException(status_code=400, detail="Invalid movement_type")

    movement = InventoryMovement(
        store_id=uuid.UUID(payload.store_id),
        product_id=product.id,
        movement_type=payload.movement_type,
        quantity=quantity,
        reason=payload.reason,
        related_order_id=uuid.UUID(payload.related_order_id) if payload.related_order_id else None,
    )
    db.add(movement)
    await db.flush()
    return product, movement


@router.get("/{store_id}")
async def get_inventory(store_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InventoryMovement, Product).join(Product, Product.id == InventoryMovement.product_id).where(InventoryMovement.store_id == uuid.UUID(store_id)).order_by(InventoryMovement.created_at.desc()))
    return [serialize_movement(movement, product) for movement, product in result.all()]


@router.post("/adjust")
async def adjust_inventory(payload: InventoryAdjustPayload, db: AsyncSession = Depends(get_db)):
    product, movement = await adjust_product_stock(db, payload)
    store = await db.get(Store, uuid.UUID(payload.store_id))
    event_type = payload.movement_type if payload.movement_type in {"stock_added", "stock_removed"} else "stock_updated"
    await emit_storefront_event(db, event_type, user_id=str(store.user_id) if store else None, store_id=payload.store_id, product_id=str(product.id), product_name=product.name, category=product.category, quantity=payload.quantity)
    if product.stock_quantity <= (product.low_stock_threshold or 0):
        await emit_storefront_event(db, "inventory_low", user_id=str(store.user_id) if store else None, store_id=payload.store_id, product_id=str(product.id), product_name=product.name, category=product.category, quantity=product.stock_quantity)
    return {**serialize_movement(movement, product), "stock_quantity": product.stock_quantity}
