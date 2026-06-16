from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.store import (
    PaymentAccount,
    ProductInStoreResponse,
    StoreDashboardResponse,
    StoreDashboardStats,
    StoreResponse,
    StoreSetupRequest,
    StoreUpdateRequest,
)
from app.services.auth_service import get_current_user
from app.services.store_generator import generate_slug
from app.utils.formatters import build_store_url

router = APIRouter(prefix="/store", tags=["business"])


@router.post("/setup", response_model=StoreResponse)
async def setup_store(
    body: StoreSetupRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    existing = await db.scalar(select(Store).where(Store.user_id == user.id))
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Business profile already exists. Use PATCH /store/me to update it.",
        )

    user.business_description = body.business_description
    if body.whatsapp_number:
        user.whatsapp_no = body.whatsapp_number

    store_name = (body.business_name or "").strip()
    if not store_name:
        store_name = (body.business_description.split(".")[0] or "Business").strip()[:100]

    store_slug = await generate_slug(store_name, db)
    store = Store(
        user_id=user.id,
        store_name=store_name[:100],
        slug=store_slug,
        store_slug=store_slug,
        business_type=body.business_type,
        instagram_handle=body.instagram_handle,
        store_description=body.business_description,
        whatsapp_number=body.whatsapp_number or user.whatsapp_no or user.phone,
        theme_config={},
        is_published=True,
    )
    db.add(store)
    user.onboarding_complete = True
    await db.commit()
    await db.refresh(store)
    return _store_response(store, [], owner=user)


@router.get("/me/dashboard", response_model=StoreDashboardResponse)
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreDashboardResponse:
    store = await _get_user_store(db, user)
    products = (
        await db.execute(
            select(Product)
            .where(Product.store_id == store.id)
            .order_by(Product.created_at.desc())
        )
    ).scalars().all()

    total_orders = await db.scalar(select(func.count(Order.id)).where(Order.store_id == store.id)) or 0
    orders_today = await db.scalar(
        select(func.count(Order.id)).where(
            Order.store_id == store.id,
            func.date(Order.created_at) == date.today(),
        )
    ) or 0
    pending_orders = await db.scalar(
        select(func.count(Order.id)).where(
            Order.store_id == store.id,
            Order.status == "pending",
        )
    ) or 0
    today_revenue = await db.scalar(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            Order.store_id == store.id,
            Order.status.in_(["paid", "delivered"]),
            func.date(Order.created_at) == date.today(),
        )
    ) or 0
    total_revenue = await db.scalar(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            Order.store_id == store.id,
            Order.status.in_(["paid", "delivered"]),
        )
    ) or 0
    low_stock_products = sum(
        1
        for product in products
        if product.stock_count is not None
        and product.stock_count <= (product.low_stock_threshold or 5)
    )

    return StoreDashboardResponse(
        store=_store_response(store, list(products), owner=user),
        stats=StoreDashboardStats(
            total_orders=int(total_orders),
            orders_today=int(orders_today),
            pending_orders=int(pending_orders),
            today_revenue=float(today_revenue),
            total_revenue=float(total_revenue),
            product_count=len(products),
            low_stock_products=low_stock_products,
        ),
    )


@router.get("/me", response_model=StoreResponse)
async def get_my_store(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    store = await _get_user_store(db, user)
    products = (
        await db.execute(select(Product).where(Product.store_id == store.id))
    ).scalars().all()
    return _store_response(store, list(products), owner=user)


@router.patch("/me", response_model=StoreResponse)
async def update_store(
    body: StoreUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    store = await _get_user_store(db, user)

    if body.store_name is not None:
        store.store_name = body.store_name
    if body.business_type is not None:
        store.business_type = body.business_type
    if body.instagram_handle is not None:
        store.instagram_handle = body.instagram_handle
    if body.store_description is not None:
        store.store_description = body.store_description
        user.business_description = body.store_description
    if body.whatsapp_number is not None:
        store.whatsapp_number = body.whatsapp_number
        user.whatsapp_no = body.whatsapp_number
    if body.theme_config is not None:
        store.theme_config = body.theme_config

    await db.commit()
    await db.refresh(store)
    products = (
        await db.execute(select(Product).where(Product.store_id == store.id))
    ).scalars().all()
    return _store_response(store, list(products), owner=user)


@router.post("/me/publish", response_model=StoreResponse)
async def publish_store(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    store = await _get_user_store(db, user)
    store.is_published = True
    await db.commit()
    await db.refresh(store)
    products = (
        await db.execute(
            select(Product).where(
                Product.store_id == store.id,
                Product.is_available.is_(True),
            )
        )
    ).scalars().all()
    return _store_response(store, list(products), owner=user)


@router.get("/{slug}", response_model=StoreResponse)
async def get_store(slug: str, db: AsyncSession = Depends(get_db)) -> StoreResponse:
    store = await db.scalar(
        select(Store).where((Store.store_slug == slug) | (Store.slug == slug))
    )
    if not store or not store.is_active:
        raise HTTPException(status_code=404, detail="Business not found")

    products = (
        await db.execute(
            select(Product).where(
                Product.store_id == store.id,
                Product.is_available.is_(True),
            )
        )
    ).scalars().all()
    owner = await db.get(User, store.user_id)
    return _store_response(store, list(products), owner=owner)


async def _get_user_store(db: AsyncSession, user: User) -> Store:
    store = await db.scalar(select(Store).where(Store.user_id == user.id))
    if not store:
        raise HTTPException(
            status_code=404,
            detail="No business profile yet. Complete setup first.",
        )
    return store


def _store_response(
    store: Store,
    products: list[Product],
    owner: User | None = None,
) -> StoreResponse:
    return StoreResponse(
        id=store.id,
        store_name=store.store_name,
        store_slug=store.store_slug or store.slug,
        business_type=store.business_type or "physical_products",
        instagram_handle=store.instagram_handle,
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
        public_url=build_store_url(store.store_slug or store.slug),
        payment_account=_payment_account(owner),
    )


def _payment_account(owner: User | None) -> PaymentAccount:
    if not owner or not owner.verified_bank_account:
        return PaymentAccount(ready=False)
    return PaymentAccount(
        bank_name=owner.verified_bank_name,
        account_name=owner.full_name,
        account_number=owner.verified_bank_account,
        ready=True,
    )
