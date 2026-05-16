from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.models.commerce import InventoryMovement, Order, OrderItem, Product, Store
from app.models.user import User
from app.campaigns.routes import find_campaign_by_ref, record_campaign_visit
from app.events.handlers import emit_event
from app.storefront.service import (
    create_order,
    create_product,
    create_store,
    generate_store_blueprint,
    normalize_store_slug,
)

router = APIRouter(prefix="/api/storefront", tags=["storefront"])


class GenerateStoreRequest(BaseModel):
    description: str


class StoreCreateRequest(BaseModel):
    user_id: str
    store_name: str
    slug: str | None = None
    tagline: str | None = None
    description: str | None = None
    template: str | None = None
    theme: str | None = None
    categories: list[str] = []
    config_json: dict | None = None
    theme_json: dict = {}
    starter_products: list[dict] = []
    contact_whatsapp: str | None = None
    has_squad_account: bool = False


class ProductCreateRequest(BaseModel):
    store_id: str
    name: str
    description: str | None = None
    category: str | None = None
    type: str = "product"
    price: float
    image_url: str | None = None
    stock_quantity: int = 0
    low_stock_threshold: int = 5


class OrderCreateRequest(BaseModel):
    store_id: str
    customer_name: str | None = None
    customer_phone: str | None = None
    items: list[dict]
    idempotency_key: str | None = None
    campaign_ref: str | None = None


class InventoryAdjustRequest(BaseModel):
    product_id: str
    quantity: int
    reason: str = "manual_adjustment"


@router.post("/ai/generate-store")
async def generate_store(payload: GenerateStoreRequest):
    return await generate_store_blueprint(payload.description)


@router.post("/stores")
async def post_store(payload: StoreCreateRequest, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, UUID(payload.user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Enforce free plan store limit
    from app.config import settings

    if getattr(user, "plan", "free") == "free":
        existing = (await db.execute(select(Store).where(Store.user_id == user.id))).scalars().all()
        if len(existing) >= settings.free_store_limit:
            raise HTTPException(status_code=403, detail="Free plan allows only one store")

    store = await create_store(db, user, payload.dict())
    user.persona_mode = "storefront_extension"
    return _store(store)


@router.get("/stores/{slug}")
async def get_store(slug: str, ref: str | None = None, session_id: str | None = None, db: AsyncSession = Depends(get_db)):
    store_slug = normalize_store_slug(slug)
    store = (await db.execute(select(Store).where(Store.slug == store_slug))).scalar_one_or_none()
    if not store:
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

    products = (await db.execute(select(Product).where(Product.store_id == store.id, Product.is_active.is_(True)))).scalars().all()
    return {
        **_store(store),
        "tenant_context": _tenant_context(store),
        "products": [_product(product) for product in products],
        "attribution": attribution,
    }


@router.get("/stores/by-user/{user_id}")
async def get_store_by_user(user_id: str, db: AsyncSession = Depends(get_db)):
    stores = (await db.execute(select(Store).where(Store.user_id == UUID(user_id)))).scalars().all()
    return [_store(store) for store in stores]


@router.put("/stores/{store_id}")
async def update_store(store_id: str, payload: dict, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Update fields from payload
    for k, v in payload.items():
        if hasattr(store, k):
            if k in ["contact_whatsapp", "whatsapp_number"] and v:
                from app.auth.routes import _normalize_whatsapp_number
                v = _normalize_whatsapp_number(v)
            setattr(store, k, v)
    
    # Special handling for config_json if provided
    if "categories" in payload or "template" in payload:
        config = store.config_json or {}
        if "categories" in payload: config["categories"] = payload["categories"]
        if "template" in payload: config["template"] = payload["template"]
        store.config_json = config

    await db.flush()
    return _store(store)


@router.post("/products")
async def post_product(payload: ProductCreateRequest, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, UUID(payload.store_id))
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    # Enforce product/service limits for free plan users
    user = await db.get(User, store.user_id)
    from app.config import settings

    # Validate type
    ptype = getattr(payload, "type", "product")

    if ptype == "product" and (payload.stock_quantity is None):
        raise HTTPException(status_code=400, detail="Products require stock_quantity")

    if getattr(user, "plan", "free") == "free":
        products = (await db.execute(select(Product).where(Product.user_id == user.id))).scalars().all()
        if len(products) >= settings.free_product_limit:
            raise HTTPException(status_code=403, detail="Free plan product limit reached")

    product = await create_product(db, store, payload.dict())
    return _product(product)


@router.get("/products/{store_id}")
async def get_products(store_id: str, db: AsyncSession = Depends(get_db)):
    products = (await db.execute(select(Product).where(Product.store_id == store_id))).scalars().all()
    return [_product(product) for product in products]


@router.get("/product/{product_id}")
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, UUID(product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _product(product)


@router.put("/products/{product_id}")
async def update_product(product_id: str, payload: dict, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, UUID(product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for k, v in payload.items():
        if hasattr(product, k):
            setattr(product, k, v)
    return _product(product)


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, UUID(product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    return {"status": "deleted", "product_id": str(product.id)}


@router.post("/orders")
async def post_order(payload: OrderCreateRequest, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, UUID(payload.store_id))
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    try:
        order = await create_order(db, store, payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _order(order)


@router.get("/orders/{store_id}")
async def get_orders(store_id: str, db: AsyncSession = Depends(get_db)):
    orders = (await db.execute(select(Order).where(Order.store_id == store_id).order_by(Order.created_at.desc()))).scalars().all()
    return [_order(order) for order in orders]


@router.get("/order/{order_id}")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, UUID(order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    data = _order(order)
    store = await db.get(Store, order.store_id)
    if store:
        data["store_slug"] = store.slug
        data["store_name"] = store.store_name
    items = (await db.execute(select(OrderItem, Product).outerjoin(Product, Product.id == OrderItem.product_id).where(OrderItem.order_id == order.id))).all()
    data["items"] = [
        {
            "id": str(item.id),
            "product_id": str(item.product_id),
            "product_name": item.product_name or (product.name if product else None),
            "quantity": item.quantity,
            "unit_price": float(item.unit_price or 0),
            "total_price": float(item.total_price or 0),
        }
        for item, product in items
    ]
    return data


@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, payload: dict, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, UUID(order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    previous_payment_status = order.payment_status
    status = payload.get("order_status") or payload.get("status")
    payment_status = payload.get("payment_status")
    if not status and not payment_status:
        raise HTTPException(status_code=400, detail="status is required")
    should_mark_paid = payment_status == "paid" or status == "paid" or payload.get("simulate_payment")
    if status:
        order.order_status = status
        order.status = status
    if payment_status and payment_status != "paid":
        order.payment_status = payment_status

    if previous_payment_status != "paid" and should_mark_paid:
        await emit_event(db, {
            "event_type": "payment_confirmed",
            "source": "storefront",
            "user_id": str(order.user_id),
            "store_id": str(order.store_id),
            "order_id": str(order.id),
            "amount": float(order.total_amount or 0),
            "reference": order.squad_payment_reference,
        })
    elif should_mark_paid:
        order.payment_status = "paid"
        order.order_status = "paid"
        order.status = "paid"
    return _order(order)


@router.get("/inventory/{store_id}")
async def get_inventory(store_id: str, db: AsyncSession = Depends(get_db)):
    products = (await db.execute(select(Product).where(Product.store_id == store_id))).scalars().all()
    return [
        {
            **_product(product),
            "is_low_stock": (product.stock_quantity or 0) <= (product.low_stock_threshold or 0),
        }
        for product in products
    ]


@router.get("/inventory/low-stock/{store_id}")
async def get_low_stock(store_id: str, db: AsyncSession = Depends(get_db)):
    products = (await db.execute(select(Product).where(Product.store_id == store_id))).scalars().all()
    low = [
        _product(p)
        for p in products
        if (p.stock_quantity or 0) <= (p.low_stock_threshold or 0)
    ]
    return low


@router.post("/inventory/adjust")
async def adjust_inventory(payload: InventoryAdjustRequest, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, UUID(payload.product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    store = await db.get(Store, product.store_id)
    product.stock_quantity = max((product.stock_quantity or 0) + payload.quantity, 0)
    db.add(InventoryMovement(
        store_id=product.store_id,
        product_id=product.id,
        movement_type="in" if payload.quantity >= 0 else "out",
        quantity=abs(payload.quantity),
        reason=payload.reason,
    ))
    await emit_event(db, {
        "event_type": "stock_added" if payload.quantity >= 0 else "stock_removed",
        "source": "storefront",
        "user_id": str(store.user_id),
        "store_id": str(store.id),
        "product_id": str(product.id),
        "quantity": payload.quantity,
    })
    return _product(product)


def _store(store: Store) -> dict:
    return {
        "id": str(store.id),
        "user_id": str(store.user_id),
        "store_name": store.store_name,
        "slug": store.slug,
        "store_slug": store.store_slug or store.slug,
        "tagline": store.tagline,
        "description": store.description,
        "theme_json": store.theme_json,
        "theme": store.theme,
        "template": store.template or "fashion",
        "config_json": store.config_json or {},
        "contact_whatsapp": store.contact_whatsapp,
        "has_squad_account": store.has_squad_account,
        "squad_virtual_account_number": store.squad_virtual_account_number,
    }


def _tenant_context(store: Store) -> dict:
    return {
        "store_id": str(store.id),
        "user_id": str(store.user_id),
        "slug": store.slug,
        "routing": "path",
    }


def _product(product: Product) -> dict:
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
    }


def _order(order: Order) -> dict:
    return {
        "id": str(order.id),
        "store_id": str(order.store_id),
        "user_id": str(order.user_id),
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "total_amount": float(order.total_amount or 0),
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "squad_payment_reference": order.squad_payment_reference,
        "campaign_ref": order.campaign_ref,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }
