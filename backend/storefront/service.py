import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Store
from app.models import Product
from app.models.user import User
from .sync import emit_storefront_event

router = APIRouter()


class StorePayload(BaseModel):
    user_id: str
    store_name: str
    slug: str
    description: str | None = None
    tagline: str | None = None
    logo_url: str | None = None
    theme_json: dict[str, Any] | None = None
    theme: str | None = None
    template: str | None = None
    config_json: dict[str, Any] | None = None
    categories: list[str] | None = None
    starter_products: list[dict[str, Any]] | None = None
    contact_whatsapp: str | None = None
    business_category: str | None = None
    pickup_delivery_note: str | None = None
    is_active: bool = True


def serialize_store(store: Store) -> dict[str, Any]:
    return {
        "id": str(store.id),
        "user_id": str(store.user_id),
        "store_name": store.store_name,
        "slug": store.slug,
        "description": store.description,
        "tagline": getattr(store, "tagline", None),
        "logo_url": store.logo_url,
        "theme_json": store.theme_json,
        "theme": getattr(store, "theme", None),
        "template": getattr(store, "template", None),
        "config_json": getattr(store, "config_json", None),
        "contact_whatsapp": store.contact_whatsapp,
        "business_category": getattr(store, "business_category", None),
        "pickup_delivery_note": getattr(store, "pickup_delivery_note", None),
        "is_active": store.is_active,
        "created_at": store.created_at.isoformat() if store.created_at else None,
        "updated_at": store.updated_at.isoformat() if store.updated_at else None,
    }


@router.post("")
async def create_store(payload: StorePayload, db: AsyncSession = Depends(get_db)):
    slug = payload.slug.lower().strip()
    exists = await db.execute(select(Store).where(Store.slug == slug))
    if exists.scalar_one_or_none():
        slug = f"{slug}-{uuid.uuid4().hex[:4]}"
    data = payload.model_dump(exclude={"categories", "starter_products"})
    data["slug"] = slug
    user_id = uuid.UUID(payload.user_id)
    user = await db.get(User, user_id)
    if user and not data.get("contact_whatsapp"):
        data["contact_whatsapp"] = user.whatsapp_no
        data["whatsapp_number"] = user.whatsapp_no
    if not data.get("config_json"):
        data["config_json"] = {
            "template": payload.template or "fashion",
            "theme": payload.theme or "default",
            "categories": payload.categories or [],
            "starter_products": payload.starter_products or [],
        }
    store = Store(**data)
    if isinstance(store.user_id, str):
        store.user_id = user_id
    db.add(store)
    await db.flush()
    for item in payload.starter_products or []:
        db.add(Product(
            store_id=store.id,
            user_id=store.user_id,
            name=item.get("name") or "Demo Product",
            description=item.get("description"),
            category=item.get("category"),
            price=item.get("price") or item.get("suggested_price") or 0,
            image_url=item.get("image_url"),
            stock_quantity=item.get("stock_quantity") if item.get("stock_quantity") is not None else item.get("stock", 10),
            low_stock_threshold=item.get("low_stock_threshold", 2),
            is_active=True,
            is_available=True,
            source="ai",
        ))
    await emit_storefront_event(db, "store_created", user_id=str(store.user_id), store_id=str(store.id))
    return serialize_store(store)


@router.get("/by-user/{user_id}")
async def get_stores_by_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Store).where(Store.user_id == uuid.UUID(user_id)).order_by(Store.created_at.desc()))
    return [serialize_store(store) for store in result.scalars().all()]


@router.get("/{slug}")
async def get_store(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Store).where(Store.slug == slug))
    store = result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return serialize_store(store)


@router.put("/{store_id}")
async def update_store(store_id: str, payload: StorePayload, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, uuid.UUID(store_id))
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key != "user_id":
            setattr(store, key, value)
    await db.flush()
    return serialize_store(store)
