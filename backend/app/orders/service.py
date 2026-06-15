import uuid
from decimal import Decimal
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderItem, Product
from app.inventory.service import decrease_stock, record_movement
from app.services import intelligence_sync
from app.whatsapp.service import send_text
from app.models.user import User
from app.whatsapp.recipients import seller_notification_recipients
from app.database import AsyncSession


async def create_order(session: AsyncSession, store_id: uuid.UUID, customer: dict, items: List[dict]) -> Order:
    order = Order(
        store_id=store_id,
        customer_name=customer.get("name"),
        customer_phone=customer.get("phone"),
        payment_status="pending",
        order_status="pending",
    )
    session.add(order)
    await session.flush()

    total = Decimal(0)
    for it in items:
        product_id = uuid.UUID(it["product_id"]) if isinstance(it.get("product_id"), str) else it.get("product_id")
        quantity = int(it.get("quantity", 1))
        # fetch product price
        q = select(Product).where(Product.id == product_id)
        res = await session.execute(q)
        prod = res.scalar_one()
        unit_price = prod.price
        line_total = Decimal(quantity) * Decimal(unit_price)
        oi = OrderItem(
            order_id=order.id,
            product_id=product_id,
            product_name=prod.name,
            quantity=quantity,
            unit_price=unit_price,
            total_price=line_total,
            subtotal=line_total,
        )
        session.add(oi)
        total += line_total
    order.total_amount = total
    await session.flush()

    # emit order_created event
    await intelligence_sync.emit_event(
        session,
        {
            "user_id": str(order.store_id),
            "store_id": str(store_id),
            "event_type": "order_created",
            "amount": float(total),
            "timestamp": None,
        },
    )

    return order


async def mark_order_paid(session: AsyncSession, order_id: uuid.UUID, squad_ref: str = None):
    q = select(Order).where(Order.id == order_id)
    res = await session.execute(q)
    order = res.scalar_one_or_none()
    if not order:
        return None
    order.payment_status = "paid"
    order.order_status = "paid"
    if squad_ref:
        order.squad_payment_reference = squad_ref
    await session.flush()

    # reduce inventory for each order item and record movements
    q2 = select(OrderItem).where(OrderItem.order_id == order.id)
    res2 = await session.execute(q2)
    items = res2.scalars().all()
    for it in items:
        await decrease_stock(session, it.product_id, it.quantity)
        await record_movement(
            session,
            store_id=order.store_id,
            product_id=it.product_id,
            movement_type="sale",
            quantity=it.quantity,
            reason=f"Order {order.id}",
            related_order_id=order.id,
        )

    await intelligence_sync.emit_event(
        session,
        {
            "user_id": str(order.store_id),
            "store_id": str(order.store_id),
            "event_type": "payment_confirmed",
            "amount": float(order.total_amount),
            "timestamp": None,
        },
    )

    # Notify store owner via WhatsApp if possible
    try:
        # fetch owner contact from store (join)
        # lazy import to avoid circular
        from app.models import Store

        q = select(Store).where(Store.id == order.store_id)
        res = await session.execute(q)
        store = res.scalar_one_or_none()
        user = await session.get(User, store.user_id) if store else None
        recipients = seller_notification_recipients(user=user, store=store)
        message = (
            f"New paid storefront order - {str(order.id)[:8]}\n"
            f"Amount: NGN {float(order.total_amount or 0):,.2f}\n"
            "Inventory has been updated."
        )
        for recipient in recipients:
            await send_text(recipient, message)
    except Exception:
        pass

    return order
