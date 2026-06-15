from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.models.customer import Customer
from app.models.inventory_movement import InventoryMovement
from app.models.notification_log import NotificationLog
from app.schemas.order import (
    OrderCreateRequest,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.services.auth_service import get_current_user
from app.services.whatsapp_client import build_wa_me_link, send_text
from app.utils.formatters import format_naira, generate_order_ref

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    body: OrderCreateRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    store = (
        await db.execute(select(Store).where(Store.store_slug == body.store_slug))
    ).scalar_one_or_none()
    if not store or not store.is_active:
        raise HTTPException(status_code=404, detail="Store not found")

    product_ids = [item.product_id for item in body.items]
    product_rows = (
        await db.execute(
            select(Product).where(
                Product.id.in_(product_ids), Product.store_id == store.id
            )
        )
    ).scalars().all()
    products_by_id = {p.id: p for p in product_rows}

    order_items_data: list[dict] = []
    total = Decimal("0")
    for item in body.items:
        product = products_by_id.get(item.product_id)
        if not product or not product.is_available:
            raise HTTPException(
                status_code=422,
                detail=f"Product {item.product_id} not available",
            )
        if product.stock_count is not None and item.quantity > product.stock_count:
            raise HTTPException(
                status_code=422,
                detail=f"Only {product.stock_count} of {product.name} in stock",
            )
        unit_price = Decimal(str(product.price))
        subtotal = unit_price * item.quantity
        order_items_data.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            }
        )
        total += subtotal

    order_ref = await generate_order_ref()
    order = Order(
        store_id=store.id,
        user_id=store.user_id,
        order_ref=order_ref,
        customer_name=body.customer_name,
        customer_whatsapp=body.customer_whatsapp,
        customer_email=body.customer_email,
        total_amount=total,
        status="pending",
        payment_status="unpaid",
        notes=body.notes,
        delivery_address=body.delivery_address,
    )
    db.add(order)
    await db.flush()

    items: list[OrderItem] = []
    for data in order_items_data:
        oi = OrderItem(
            order_id=order.id,
            product_id=data["product_id"],
            product_name=data["product_name"],
            quantity=data["quantity"],
            unit_price=data["unit_price"],
            subtotal=data["subtotal"],
        )
        db.add(oi)
        items.append(oi)
        product = products_by_id.get(data["product_id"])
        if product and product.stock_count is not None:
            product.stock_count = max(product.stock_count - data["quantity"], 0)
            db.add(
                InventoryMovement(
                    store_id=store.id,
                    product_id=product.id,
                    movement_type="order",
                    quantity=-data["quantity"],
                    reason=f"Order {order_ref}",
                    related_order_id=order.id,
                )
            )

    await _upsert_customer(db, store.id, order.customer_name, order.customer_whatsapp)
    db.add(
        NotificationLog(
            user_id=store.user_id,
            business_id=store.id,
            type="new_order",
            channel="dashboard",
            message=f"New order {order_ref} from {order.customer_name or 'Customer'}",
            content=f"New order {order_ref} from {order.customer_name or 'Customer'}",
            delivered=False,
        )
    )

    await db.commit()
    await db.refresh(order)

    background.add_task(
        _notify_trader_new_order, str(order.id)
    )

    return _to_response(order, items)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderListResponse:
    store = (
        await db.execute(select(Store).where(Store.user_id == user.id))
    ).scalar_one_or_none()
    if not store:
        return OrderListResponse(orders=[], total=0, limit=limit, offset=offset)

    where = [Order.store_id == store.id]
    if status:
        where.append(Order.status == status)

    total = await db.scalar(
        select(func.count(Order.id)).where(*where)
    ) or 0

    rows = (
        await db.execute(
            select(Order)
            .where(*where)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()

    order_ids = [o.id for o in rows]
    items_by_order: dict[uuid.UUID, list[OrderItem]] = {}
    if order_ids:
        item_rows = (
            await db.execute(
                select(OrderItem).where(OrderItem.order_id.in_(order_ids))
            )
        ).scalars().all()
        for item in item_rows:
            items_by_order.setdefault(item.order_id, []).append(item)

    return OrderListResponse(
        orders=[_to_response(o, items_by_order.get(o.id, [])) for o in rows],
        total=int(total),
        limit=limit,
        offset=offset,
    )


@router.post("/manual", response_model=OrderResponse, status_code=201)
async def create_manual_order(
    body: OrderCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    store = (
        await db.execute(select(Store).where(Store.user_id == user.id))
    ).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Complete business setup first")
    body.store_slug = store.store_slug or store.slug
    return await create_order(body, BackgroundTasks(), db)


@router.get("/{order_ref}", response_model=OrderResponse)
async def get_order(
    order_ref: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    order = (
        await db.execute(select(Order).where(Order.order_ref == order_ref))
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Scope: trader can only see their own store's orders
    store = (
        await db.execute(select(Store).where(Store.id == order.store_id))
    ).scalar_one_or_none()
    if not store or store.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    items = (
        await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    ).scalars().all()
    return _to_response(order, list(items))


@router.patch("/{order_ref}/status", response_model=OrderResponse)
async def update_order_status(
    order_ref: str,
    body: OrderStatusUpdate,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    order = (
        await db.execute(select(Order).where(Order.order_ref == order_ref))
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    store = (
        await db.execute(select(Store).where(Store.id == order.store_id))
    ).scalar_one_or_none()
    if not store or store.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = body.status
    if body.status in {"paid", "delivered"}:
        order.payment_status = "paid"
    if body.status in {"pending", "cancelled"}:
        order.payment_status = "unpaid"
    db.add(
        NotificationLog(
            user_id=user.id,
            business_id=store.id,
            type="order_status",
            channel="dashboard",
            message=f"{order.order_ref} marked {body.status}",
            content=f"{order.order_ref} marked {body.status}",
            delivered=False,
        )
    )
    await db.commit()
    await db.refresh(order)

    items = (
        await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    ).scalars().all()

    # Note: per CLAUDE.md §11, the bot does NOT message the buyer on status
    # changes. The trader uses the wa.me deep link in the original
    # transfer-claimed notification to message the buyer from their personal
    # WhatsApp.

    return _to_response(order, list(items))


@router.patch("/{order_ref}/claim-transfer", response_model=OrderResponse)
async def claim_transfer(
    order_ref: str,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """Buyer signals they have transferred the order amount.

    Public, no auth — called from the storefront checkout's "I've
    Transferred" button. Idempotent on ``transfer_claimed``: re-claiming
    is a no-op success and does NOT re-notify the trader.
    """
    order = (
        await db.execute(select(Order).where(Order.order_ref == order_ref))
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = (
        await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    ).scalars().all()

    if order.status == "transfer_claimed":
        return _to_response(order, list(items))
    if order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Order is currently {order.status} — cannot claim transfer.",
        )

    order.status = "transfer_claimed"
    await db.commit()
    await db.refresh(order)

    background.add_task(_notify_trader_transfer_claimed, str(order.id))

    return _to_response(order, list(items))


def _to_response(order: Order, items: list[OrderItem]) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        order_ref=order.order_ref,
        store_id=order.store_id,
        customer_name=order.customer_name,
        customer_whatsapp=order.customer_whatsapp,
        customer_email=order.customer_email,
        total_amount=float(order.total_amount or 0),
        status=order.status,
        payment_status=order.payment_status,
        payment_link=order.payment_link,
        notes=order.notes,
        delivery_address=order.delivery_address,
        items=[
            OrderItemResponse(
                id=i.id,
                product_id=i.product_id,
                product_name=i.product_name,
                quantity=i.quantity,
                unit_price=float(i.unit_price or 0),
                subtotal=float(i.subtotal or 0),
            )
            for i in items
        ],
        created_at=order.created_at,
    )


async def _upsert_customer(
    db: AsyncSession,
    business_id: uuid.UUID,
    name: str | None,
    phone: str | None,
) -> None:
    if not phone:
        return
    customer = await db.scalar(
        select(Customer).where(
            Customer.business_id == business_id,
            Customer.phone == phone,
        )
    )
    if customer is None:
        customer = Customer(
            business_id=business_id,
            name=(name or "Customer")[:100],
            phone=phone,
            total_orders=1,
        )
        db.add(customer)
    else:
        customer.name = (name or customer.name)[:100]
        customer.total_orders = (customer.total_orders or 0) + 1
    customer.last_purchase = func.now()


async def _notify_trader_new_order(order_id: str) -> None:
    """BackgroundTask: WhatsApp the trader when a new order is placed.

    Sent the moment the order is created (status=pending). The richer
    notification with deep link goes out when the buyer claims the transfer
    — see :func:`_notify_trader_transfer_claimed`.
    """
    try:
        async with AsyncSessionLocal() as db:
            order = await db.get(Order, uuid.UUID(order_id))
            if not order:
                return
            user = await db.get(User, order.user_id)
            if not user or not user.whatsapp_no:
                return
            await send_text(
                user.whatsapp_no,
                f"🛒 New order on your store!\n\n"
                f"Order: {order.order_ref}\n"
                f"Customer: {order.customer_name or 'Guest'}\n"
                f"Total: {format_naira(float(order.total_amount or 0))}\n\n"
                f"The customer will transfer to your bank account. "
                f"You'll get another alert when they confirm the transfer.",
            )
    except Exception:
        logger.exception("Failed to notify trader of new order %s", order_id)


async def _notify_trader_transfer_claimed(order_id: str) -> None:
    """BackgroundTask: WhatsApp the trader when a buyer has clicked
    "I've Transferred". Includes:

    - order ref, customer name, items, amount
    - bank last-4 ("check your {bank_name} ending {last4}")
    - wa.me/{buyer_phone}?text=... deep link the trader taps to message the
      buyer from THEIR personal WhatsApp (CLAUDE.md §11)
    - confirm/reject reply hint
    """
    try:
        async with AsyncSessionLocal() as db:
            order = await db.get(Order, uuid.UUID(order_id))
            if not order:
                return
            user = await db.get(User, order.user_id)
            if not user or not user.whatsapp_no:
                return

            store = await db.get(Store, order.store_id)
            items = (
                await db.execute(
                    select(OrderItem).where(OrderItem.order_id == order.id)
                )
            ).scalars().all()
            item_summary = (
                ", ".join(f"{i.quantity}× {i.product_name}" for i in items) or "items"
            )

            account = (user.verified_bank_account or "").strip()
            bank_label = (user.verified_bank_name or "your bank").strip()
            bank_line = (
                f"Check your {bank_label} account ending {account[-4:]} for the transfer."
                if account
                else "Check your bank account for the transfer."
            )

            message = (
                f"💸 New transfer claim — {order.order_ref}\n\n"
                f"Customer: {order.customer_name or 'Guest'}\n"
                f"Amount: {format_naira(float(order.total_amount or 0))}\n"
                f"Items: {item_summary}\n\n"
                f"{bank_line}\n\n"
                f"When you've checked:\n"
                f"✅ Reply *confirm {order.order_ref}* if received\n"
                f"❌ Reply *reject {order.order_ref}* if not received"
            )

            if order.customer_whatsapp and store:
                first_name = (order.customer_name or "there").split()[0]
                prefilled = (
                    f"Hi {first_name}! This is {store.store_name}. "
                    f"We're checking your payment for order {order.order_ref} "
                    f"({item_summary}, total "
                    f"{format_naira(float(order.total_amount or 0))})."
                )
                link = build_wa_me_link(order.customer_whatsapp, prefilled)
                if link:
                    message += (
                        f"\n\n💬 Message {order.customer_name or 'the buyer'} "
                        f"directly:\n{link}"
                    )

            await send_text(user.whatsapp_no, message)
    except Exception:
        logger.exception("Failed to notify trader of transfer claim %s", order_id)
