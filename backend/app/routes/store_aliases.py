from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.commerce import Order, Product, Store
from app.routes.marketing import find_campaign_by_ref, record_campaign_visit
from app.services.storefront import create_order, create_product, normalize_store_slug

router = APIRouter(tags=["store-compat"])


class StoreOrderRequest(BaseModel):
    store_slug: str
    customer_name: str | None = None
    customer_whatsapp: str | None = None
    items: list[dict]
    notes: str | None = None
    campaign_ref: str | None = None


class ProductRequest(BaseModel):
    store_id: str
    name: str
    description: str | None = None
    price: float
    category: str | None = None
    image_url: str | None = None
    stock_quantity: int = 0
    source: str = "web"


@router.get("/store/{slug}")
async def public_store(slug: str, ref: str | None = None, session_id: str | None = None, db: AsyncSession = Depends(get_db)):
    store_slug = normalize_store_slug(slug)
    store = (await db.execute(select(Store).where((Store.slug == store_slug) | (Store.store_slug == store_slug)))).scalar_one_or_none()
    if not store or not store.is_active:
        raise HTTPException(status_code=404, detail="Store not found")
    attribution = None
    if ref:
        campaign = await find_campaign_by_ref(db, store.id, ref)
        if campaign:
            await record_campaign_visit(db, campaign, session_id)
            await db.commit()
            attribution = {
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.campaign_name,
                "source": campaign.source,
                "ref_slug": campaign.ref_slug,
            }
    products = (await db.execute(select(Product).where(Product.store_id == store.id, Product.is_available.is_(True)))).scalars().all()
    return {
        "id": str(store.id),
        "user_id": str(store.user_id),
        "tenant_context": {
            "store_id": str(store.id),
            "user_id": str(store.user_id),
            "slug": store.slug,
            "routing": "path",
        },
        "store_name": store.store_name,
        "store_slug": store.store_slug or store.slug,
        "store_description": store.store_description or store.description,
        "whatsapp_number": store.whatsapp_number or store.contact_whatsapp,
        "theme": store.theme,
        "products": [_product(product) for product in products],
        "attribution": attribution,
    }


@router.get("/store/me/{user_id}")
async def store_me(user_id: str, db: AsyncSession = Depends(get_db)):
    stores = (await db.execute(select(Store).where(Store.user_id == user_id))).scalars().all()
    return [
        {
            "id": str(store.id),
            "store_name": store.store_name,
            "store_slug": store.store_slug or store.slug,
            "store_description": store.store_description or store.description,
            "theme": store.theme,
            "has_squad_account": store.has_squad_account,
            "squad_virtual_account_number": store.squad_virtual_account_number,
        }
        for store in stores
    ]


@router.get("/products/{store_id}")
async def list_products(store_id: str, db: AsyncSession = Depends(get_db)):
    products = (await db.execute(select(Product).where(Product.store_id == store_id))).scalars().all()
    return [_product(product) for product in products]


@router.post("/products")
async def add_product(payload: ProductRequest, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, payload.store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    product = await create_product(db, store, payload.dict())
    return _product(product)


@router.post("/orders")
async def create_public_order(payload: StoreOrderRequest, db: AsyncSession = Depends(get_db)):
    store_slug = normalize_store_slug(payload.store_slug)
    store = (await db.execute(select(Store).where((Store.slug == store_slug) | (Store.store_slug == store_slug)))).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    order = await create_order(db, store, {
        "customer_name": payload.customer_name,
        "customer_phone": payload.customer_whatsapp,
        "customer_whatsapp": payload.customer_whatsapp,
        "items": payload.items,
        "notes": payload.notes,
        "campaign_ref": payload.campaign_ref,
    })
    return {
        "id": str(order.id),
        "total_amount": float(order.total_amount or 0),
        "status": order.status,
        "squad_payment_reference": order.squad_payment_reference,
        "virtual_account_number": store.squad_virtual_account_number,
    }


@router.get("/orders/{store_id}")
async def list_orders(store_id: str, db: AsyncSession = Depends(get_db)):
    orders = (await db.execute(select(Order).where(Order.store_id == store_id).order_by(Order.created_at.desc()))).scalars().all()
    return [
        {
            "id": str(order.id),
            "customer_name": order.customer_name,
            "customer_whatsapp": order.customer_whatsapp,
            "total_amount": float(order.total_amount or 0),
            "status": order.status,
            "payment_status": order.payment_status,
            "created_at": order.created_at,
        }
        for order in orders
    ]


def _product(product: Product) -> dict:
    return {
        "id": str(product.id),
        "store_id": str(product.store_id),
        "user_id": str(product.user_id) if product.user_id else None,
        "name": product.name,
        "description": product.description,
        "price": float(product.price or 0),
        "category": product.category,
        "image_url": product.image_url,
        "is_available": product.is_available,
        "source": product.source,
        "stock_quantity": product.stock_quantity,
    }
