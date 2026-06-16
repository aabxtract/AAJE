from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.inventory_movement import InventoryMovement
from app.models.notification_log import NotificationLog
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.product import ProductResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/inventory", tags=["inventory"])


class StockAdjustRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(description="Positive to add stock, negative to remove stock")
    reason: str | None = Field(default=None, max_length=250)


@router.get("", response_model=list[ProductResponse])
async def list_inventory(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProductResponse]:
    store = await _get_user_store(db, user)
    rows = (
        await db.execute(
            select(Product)
            .where(Product.store_id == store.id)
            .order_by(Product.name.asc())
        )
    ).scalars().all()
    return [ProductResponse.model_validate(row) for row in rows]


@router.get("/low-stock", response_model=list[ProductResponse])
async def list_low_stock(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProductResponse]:
    products = await list_inventory(user=user, db=db)
    return [
        product
        for product in products
        if product.stock_count is not None
        and product.stock_count <= (product.low_stock_threshold or 5)
    ]


@router.post("/adjust", response_model=ProductResponse)
async def adjust_inventory(
    body: StockAdjustRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    store = await _get_user_store(db, user)
    product = await db.get(Product, body.product_id)
    if not product or product.store_id != store.id:
        raise HTTPException(status_code=404, detail="Product not found")

    current = product.stock_count or 0
    product.stock_count = max(current + body.quantity, 0)
    db.add(
        InventoryMovement(
            store_id=store.id,
            product_id=product.id,
            movement_type="adjustment",
            quantity=body.quantity,
            reason=body.reason,
        )
    )
    if product.stock_count <= (product.low_stock_threshold or 5):
        message = f"Low stock: {product.name} has {product.stock_count} left"
        db.add(
            NotificationLog(
                user_id=user.id,
                business_id=store.id,
                type="low_stock",
                channel="dashboard",
                message=message,
                content=message,
                delivered=False,
            )
        )
    await db.commit()
    await db.refresh(product)
    return ProductResponse.model_validate(product)


async def _get_user_store(db: AsyncSession, user: User) -> Store:
    store = await db.scalar(select(Store).where(Store.user_id == user.id))
    if not store:
        raise HTTPException(status_code=404, detail="Complete business setup first")
    return store
