from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


async def _get_user_store(db: AsyncSession, user: User) -> Store:
    store = (
        await db.execute(select(Store).where(Store.user_id == user.id))
    ).scalar_one_or_none()
    if not store:
        raise HTTPException(
            status_code=404,
            detail="No store yet. POST /store/setup to create one.",
        )
    return store


async def _load_owned_product(
    db: AsyncSession, product_id: uuid.UUID, store: Store
) -> Product:
    product = await db.get(Product, product_id)
    if not product or product.store_id != store.id:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("", response_model=list[ProductResponse])
async def list_products(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProductResponse]:
    store = await _get_user_store(db, user)
    rows = (
        await db.execute(
            select(Product)
            .where(Product.store_id == store.id)
            .order_by(Product.created_at.desc())
        )
    ).scalars().all()
    return [ProductResponse.model_validate(p) for p in rows]


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    body: ProductCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    store = await _get_user_store(db, user)
    product = Product(
        store_id=store.id,
        user_id=user.id,
        name=body.name,
        description=body.description,
        price=Decimal(str(body.price)),
        category=body.category,
        stock_count=body.stock_count,
        low_stock_threshold=body.low_stock_threshold,
        image_url=body.image_url,
        source="web",
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return ProductResponse.model_validate(product)


@router.post("/bulk", response_model=list[ProductResponse], status_code=201)
async def create_products_bulk(
    body: list[ProductCreate],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProductResponse]:
    if not body:
        raise HTTPException(status_code=422, detail="At least one product required")
    if len(body) > 100:
        raise HTTPException(status_code=422, detail="Max 100 products per request")

    store = await _get_user_store(db, user)
    created: list[Product] = []
    for item in body:
        product = Product(
            store_id=store.id,
            user_id=user.id,
            name=item.name,
            description=item.description,
            price=Decimal(str(item.price)),
            category=item.category,
            stock_count=item.stock_count,
            low_stock_threshold=item.low_stock_threshold,
            image_url=item.image_url,
            source="web",
        )
        db.add(product)
        created.append(product)
    await db.commit()
    for p in created:
        await db.refresh(p)
    return [ProductResponse.model_validate(p) for p in created]


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    store = await _get_user_store(db, user)
    product = await _load_owned_product(db, product_id, store)

    if body.name is not None:
        product.name = body.name
    if body.description is not None:
        product.description = body.description
    if body.price is not None:
        product.price = Decimal(str(body.price))
    if body.category is not None:
        product.category = body.category
    if body.stock_count is not None:
        product.stock_count = body.stock_count
    if body.low_stock_threshold is not None:
        product.low_stock_threshold = body.low_stock_threshold
    if body.image_url is not None:
        product.image_url = body.image_url
    if body.is_available is not None:
        product.is_available = body.is_available

    await db.commit()
    await db.refresh(product)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft delete: sets is_available=False. Order history keeps the
    product_name snapshot in order_items, so this is safe."""
    store = await _get_user_store(db, user)
    product = await _load_owned_product(db, product_id, store)
    product.is_available = False
    await db.commit()
