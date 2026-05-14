import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product, Store
from .sync import emit_storefront_event

router = APIRouter()


class ProductPayload(BaseModel):
    store_id: str
    name: str
    description: str | None = None
    category: str | None = None
    price: float = 0
    image_url: str | None = None
    stock_quantity: int = 0
    low_stock_threshold: int = 0
    is_active: bool = True


def serialize_product(product: Product) -> dict[str, Any]:
    return {
        "id": str(product.id),
        "store_id": str(product.store_id),
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price": float(product.price or 0),
        "image_url": product.image_url,
        "stock_quantity": product.stock_quantity,
        "low_stock_threshold": product.low_stock_threshold,
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


async def _resolve_store_id(db: AsyncSession, value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        result = await db.execute(select(Store).where(Store.slug == value))
        store = result.scalar_one_or_none()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        return store.id


@router.post("")
async def create_product(payload: ProductPayload, db: AsyncSession = Depends(get_db)):
    product = Product(**{**payload.model_dump(), "store_id": uuid.UUID(payload.store_id)})
    db.add(product)
    await db.flush()
    store = await db.get(Store, product.store_id)
    await emit_storefront_event(
        db,
        "product_created",
        user_id=str(store.user_id) if store else None,
        store_id=str(product.store_id),
        product_id=str(product.id),
        product_name=product.name,
        category=product.category,
        quantity=product.stock_quantity,
        amount=float(product.price or 0),
    )
    return serialize_product(product)


@router.get("/{store_id}")
async def list_products(store_id: str, db: AsyncSession = Depends(get_db)):
    resolved_store_id = await _resolve_store_id(db, store_id)
    result = await db.execute(select(Product).where(Product.store_id == resolved_store_id).order_by(Product.created_at.desc()))
    return [serialize_product(product) for product in result.scalars().all()]


@router.put("/{product_id}")
async def update_product(product_id: str, payload: ProductPayload, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, uuid.UUID(product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key != "store_id":
            setattr(product, key, value)
    await db.flush()
    store = await db.get(Store, product.store_id)
    await emit_storefront_event(db, "product_updated", user_id=str(store.user_id) if store else None, store_id=str(product.store_id), product_id=str(product.id), product_name=product.name, category=product.category)
    return serialize_product(product)


@router.delete("/{product_id}")
async def delete_product(product_id: str, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, uuid.UUID(product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    await db.flush()
    return {"ok": True}
