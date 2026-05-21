from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.order import Order
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.store import (
    ProductInStoreResponse,
    StoreDashboardResponse,
    StoreDashboardStats,
    StoreResponse,
    StoreSetupRequest,
    StoreUpdateRequest,
)
from app.services.auth_service import get_current_user
from app.services.store_generator import generate_slug, generate_store_from_description

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/store", tags=["store"])


@router.post("/setup", response_model=StoreResponse)
async def setup_store(
    body: StoreSetupRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    existing = await db.execute(select(Store).where(Store.user_id == user.id))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="You already have a store. Use PATCH /store/me to update it.",
        )

    user.business_description = body.business_description

    config = await generate_store_from_description(body.business_description)

    slug_seed = config.get("suggested_slug") or config.get("store_name") or "store"
    store_slug = await generate_slug(slug_seed, db)

    store = Store(
        user_id=user.id,
        store_name=config["store_name"],
        store_slug=store_slug,
        store_description=config.get("store_description"),
        whatsapp_number=user.whatsapp_no,
        theme_config=config.get("theme_config") or {},
        is_published=False,
    )
    db.add(store)
    await db.flush()

    products: list[Product] = []
    for raw in config.get("products") or []:
        if not isinstance(raw, dict):
            continue
        try:
            price = Decimal(str(raw.get("suggested_price") or 0))
            if price <= 0:
                continue
        except (InvalidOperation, ValueError):
            continue
        product = Product(
            store_id=store.id,
            user_id=user.id,
            name=str(raw.get("name") or "Product")[:200],
            description=(raw.get("short_description") or None),
            price=price,
            category=(raw.get("category") or None),
            source="ai_generated",
        )
        db.add(product)
        products.append(product)

    user.onboarding_complete = True
    await db.commit()
    await db.refresh(store)

    return _store_response(store, products)


@router.get("/{slug}", response_model=StoreResponse)
async def get_store(slug: str, db: AsyncSession = Depends(get_db)) -> StoreResponse:
    result = await db.execute(select(Store).where(Store.store_slug == slug))
    store = result.scalar_one_or_none()
    if not store or not store.is_active:
        raise HTTPException(status_code=404, detail="Store not found")

    products = (
        await db.execute(
            select(Product).where(
                Product.store_id == store.id, Product.is_available.is_(True)
            )
        )
    ).scalars().all()

    return _store_response(store, list(products))


@router.get("/me/dashboard", response_model=StoreDashboardResponse)
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreDashboardResponse:
    store = (
        await db.execute(select(Store).where(Store.user_id == user.id))
    ).scalar_one_or_none()
    if not store:
        raise HTTPException(
            status_code=404,
            detail="No store yet. POST /store/setup to create one.",
        )

    products = (
        await db.execute(select(Product).where(Product.store_id == store.id))
    ).scalars().all()

    total_orders = (
        await db.scalar(select(func.count(Order.id)).where(Order.store_id == store.id))
        or 0
    )
    pending_orders = (
        await db.scalar(
            select(func.count(Order.id)).where(
                Order.store_id == store.id, Order.status == "pending"
            )
        )
        or 0
    )
    today_revenue = (
        await db.scalar(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.store_id == store.id,
                Order.payment_status == "paid",
                func.date(Order.created_at) == date.today(),
            )
        )
        or 0
    )
    total_revenue = (
        await db.scalar(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.store_id == store.id, Order.payment_status == "paid"
            )
        )
        or 0
    )

    return StoreDashboardResponse(
        store=_store_response(store, list(products)),
        stats=StoreDashboardStats(
            total_orders=int(total_orders),
            pending_orders=int(pending_orders),
            today_revenue=float(today_revenue),
            total_revenue=float(total_revenue),
            product_count=len(products),
        ),
    )


@router.patch("/me", response_model=StoreResponse)
async def update_store(
    body: StoreUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    store = (
        await db.execute(select(Store).where(Store.user_id == user.id))
    ).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="No store yet")

    if body.store_name is not None:
        store.store_name = body.store_name
    if body.store_description is not None:
        store.store_description = body.store_description
    if body.whatsapp_number is not None:
        store.whatsapp_number = body.whatsapp_number
    if body.theme_config is not None:
        store.theme_config = body.theme_config

    await db.commit()
    await db.refresh(store)

    products = (
        await db.execute(select(Product).where(Product.store_id == store.id))
    ).scalars().all()

    return _store_response(store, list(products))


@router.post("/me/publish", response_model=StoreResponse)
async def publish_store(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    store = (
        await db.execute(select(Store).where(Store.user_id == user.id))
    ).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="No store yet")

    store.is_published = True
    await db.commit()
    await db.refresh(store)

    products = (
        await db.execute(
            select(Product).where(
                Product.store_id == store.id, Product.is_available.is_(True)
            )
        )
    ).scalars().all()

    return _store_response(store, list(products))


def _store_response(store: Store, products: list[Product]) -> StoreResponse:
    frontend = (settings.frontend_url or "https://aaje.store").rstrip("/")
    return StoreResponse(
        id=store.id,
        store_name=store.store_name,
        store_slug=store.store_slug,
        store_description=store.store_description,
        whatsapp_number=store.whatsapp_number,
        theme_config=store.theme_config or {},
        logo_url=store.logo_url,
        banner_url=store.banner_url,
        is_active=store.is_active,
        is_published=store.is_published,
        products=[
            ProductInStoreResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                price=float(p.price or 0),
                category=p.category,
                image_url=p.image_url,
                stock_count=p.stock_count,
                is_available=p.is_available,
            )
            for p in products
        ],
        public_url=f"{frontend}/store/{store.store_slug}",
    )
