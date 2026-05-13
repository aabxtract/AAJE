from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.commerce import InventoryMovement, Order, Product, Store
from app.models.user import User
from app.services.events import emit_event
from app.services.storefront import create_order, create_product, create_store, generate_store_blueprint

router = APIRouter(prefix="/api/storefront", tags=["storefront"])


class GenerateStoreRequest(BaseModel):
    description: str


class StoreCreateRequest(BaseModel):
    user_id: str
    store_name: str
    slug: str | None = None
    tagline: str | None = None
    description: str | None = None
    theme_json: dict = {}
    starter_products: list[dict] = []
    has_squad_account: bool = False


class ProductCreateRequest(BaseModel):
    store_id: str
    name: str
    description: str | None = None
    category: str | None = None
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


class InventoryAdjustRequest(BaseModel):
    product_id: str
    quantity: int
    reason: str = "manual_adjustment"


@router.post("/ai/generate-store")
async def generate_store(payload: GenerateStoreRequest):
    return await generate_store_blueprint(payload.description)


@router.post("/stores")
async def post_store(payload: StoreCreateRequest, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    store = await create_store(db, user, payload.dict())
    user.persona_mode = "storefront_extension"
    return _store(store)


@router.get("/stores/{slug}")
async def get_store(slug: str, db: AsyncSession = Depends(get_db)):
    store = (await db.execute(select(Store).where(Store.slug == slug))).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    products = (await db.execute(select(Product).where(Product.store_id == store.id, Product.is_active.is_(True)))).scalars().all()
    return {**_store(store), "products": [_product(product) for product in products]}


@router.get("/stores/by-user/{user_id}")
async def get_store_by_user(user_id: str, db: AsyncSession = Depends(get_db)):
    stores = (await db.execute(select(Store).where(Store.user_id == user_id))).scalars().all()
    return [_store(store) for store in stores]


@router.post("/products")
async def post_product(payload: ProductCreateRequest, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, payload.store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    product = await create_product(db, store, payload.dict())
    return _product(product)


@router.get("/products/{store_id}")
async def get_products(store_id: str, db: AsyncSession = Depends(get_db)):
    products = (await db.execute(select(Product).where(Product.store_id == store_id))).scalars().all()
    return [_product(product) for product in products]


@router.post("/orders")
async def post_order(payload: OrderCreateRequest, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, payload.store_id)
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


@router.post("/inventory/adjust")
async def adjust_inventory(payload: InventoryAdjustRequest, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, payload.product_id)
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
        "tagline": store.tagline,
        "description": store.description,
        "theme_json": store.theme_json,
        "contact_whatsapp": store.contact_whatsapp,
        "has_squad_account": store.has_squad_account,
        "squad_virtual_account_number": store.squad_virtual_account_number,
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
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "total_amount": float(order.total_amount or 0),
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "squad_payment_reference": order.squad_payment_reference,
    }
