import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Order, OrderItem, Product, Store
from .inventory import InventoryAdjustPayload, adjust_product_stock
from .sync import emit_storefront_event

router = APIRouter()


class OrderItemPayload(BaseModel):
    product_id: str
    quantity: int = 1
    unit_price: float | None = None
    total_price: float | None = None


class OrderPayload(BaseModel):
    store_id: str
    customer_name: str
    customer_phone: str
    total_amount: float | None = None
    payment_status: str = "pending"
    order_status: str = "pending"
    squad_payment_reference: str | None = None
    items: list[OrderItemPayload]


class OrderStatusPayload(BaseModel):
    status: str | None = None
    order_status: str | None = None
    payment_status: str | None = None
    squad_payment_reference: str | None = None
    simulate_payment: bool = False


def serialize_order(order: Order, items: list[tuple[OrderItem, Product | None]] | None = None, store: Store | None = None) -> dict[str, Any]:
    return {
        "id": str(order.id),
        "store_id": str(order.store_id),
        "store_slug": store.slug if store else None,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "total_amount": float(order.total_amount or 0),
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "squad_payment_reference": order.squad_payment_reference,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "items": [
            {
                "id": str(item.id),
                "order_id": str(item.order_id),
                "product_id": str(item.product_id),
                "product_name": product.name if product else None,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price or 0),
                "total_price": float(item.total_price or 0),
            }
            for item, product in (items or [])
        ],
    }


async def _order_items(db: AsyncSession, order_id: uuid.UUID) -> list[tuple[OrderItem, Product | None]]:
    result = await db.execute(select(OrderItem, Product).outerjoin(Product, Product.id == OrderItem.product_id).where(OrderItem.order_id == order_id))
    return list(result.all())


@router.post("")
async def create_order(payload: OrderPayload, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, uuid.UUID(payload.store_id))
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    order = Order(
        store_id=store.id,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        payment_status=payload.payment_status,
        order_status=payload.order_status,
        squad_payment_reference=payload.squad_payment_reference,
        total_amount=0,
    )
    db.add(order)
    await db.flush()

    total = 0.0
    for item in payload.items:
        product = await db.get(Product, uuid.UUID(item.product_id))
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"{product.name} is out of stock")
        unit_price = float(item.unit_price if item.unit_price is not None else product.price or 0)
        line_total = float(item.total_price if item.total_price is not None else unit_price * item.quantity)
        total += line_total
        db.add(OrderItem(order_id=order.id, product_id=product.id, quantity=item.quantity, unit_price=unit_price, total_price=line_total))
    order.total_amount = payload.total_amount if payload.total_amount is not None else total
    await db.flush()
    await emit_storefront_event(db, "order_created", user_id=str(store.user_id), store_id=str(store.id), order_id=str(order.id), amount=float(order.total_amount or 0))
    return serialize_order(order, await _order_items(db, order.id), store)


@router.get("/detail/{order_id}")
async def get_order_detail(order_id: str, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, uuid.UUID(order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    store = await db.get(Store, order.store_id)
    return serialize_order(order, await _order_items(db, order.id), store)


@router.get("/{store_id}")
async def list_orders(store_id: str, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, uuid.UUID(store_id))
    result = await db.execute(select(Order).where(Order.store_id == uuid.UUID(store_id)).order_by(Order.created_at.desc()))
    orders = []
    for order in result.scalars().all():
        orders.append(serialize_order(order, await _order_items(db, order.id), store))
    return orders


@router.put("/{order_id}/status")
async def update_order_status(order_id: str, payload: OrderStatusPayload, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, uuid.UUID(order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    store = await db.get(Store, order.store_id)
    previous_payment = order.payment_status
    next_status = payload.status or payload.order_status
    if next_status:
        order.order_status = next_status
    if payload.payment_status:
        order.payment_status = payload.payment_status
    elif payload.status == "paid" or payload.simulate_payment:
        order.payment_status = "paid"
        order.order_status = "paid"
    if payload.squad_payment_reference:
        order.squad_payment_reference = payload.squad_payment_reference

    if previous_payment != "paid" and order.payment_status == "paid":
        items = await _order_items(db, order.id)
        for item, product in items:
            if not product:
                continue
            await adjust_product_stock(
                db,
                InventoryAdjustPayload(
                    store_id=str(order.store_id),
                    product_id=str(product.id),
                    movement_type="order_paid",
                    quantity=item.quantity,
                    reason=f"Order {order.id}",
                    related_order_id=str(order.id),
                ),
            )
            await emit_storefront_event(db, "inventory_reduced", user_id=str(store.user_id) if store else None, store_id=str(order.store_id), order_id=str(order.id), product_id=str(product.id), product_name=product.name, category=product.category, quantity=item.quantity)
            if product.stock_quantity <= (product.low_stock_threshold or 0):
                await emit_storefront_event(db, "inventory_low", user_id=str(store.user_id) if store else None, store_id=str(order.store_id), product_id=str(product.id), product_name=product.name, category=product.category, quantity=product.stock_quantity)
        await emit_storefront_event(db, "payment_confirmed", user_id=str(store.user_id) if store else None, store_id=str(order.store_id), order_id=str(order.id), amount=float(order.total_amount or 0))
        await emit_storefront_event(db, "order_paid", user_id=str(store.user_id) if store else None, store_id=str(order.store_id), order_id=str(order.id), amount=float(order.total_amount or 0))
    elif order.order_status == "cancelled":
        await emit_storefront_event(db, "order_cancelled", user_id=str(store.user_id) if store else None, store_id=str(order.store_id), order_id=str(order.id), amount=float(order.total_amount or 0))

    await db.flush()
    return serialize_order(order, await _order_items(db, order.id), store)
