import uuid

from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, InventoryMovement
from app.services.whatsapp_client import send_text
from app.models import Product as ProductModel
from app.models import Store as StoreModel


async def record_movement(
    session: AsyncSession,
    store_id: uuid.UUID,
    product_id: uuid.UUID,
    movement_type: str,
    quantity: int,
    reason: str = None,
    related_order_id: uuid.UUID = None,
):
    mv = InventoryMovement(
        store_id=store_id,
        product_id=product_id,
        movement_type=movement_type,
        quantity=quantity,
        reason=reason,
        related_order_id=related_order_id,
    )
    session.add(mv)
    await session.flush()
    return mv


async def decrease_stock(session: AsyncSession, product_id: uuid.UUID, qty: int):
    # atomically decrease stock
    q = select(Product).where(Product.id == product_id)
    res = await session.execute(q)
    prod = res.scalar_one_or_none()
    if not prod:
        return None
    if prod.stock_quantity - qty < 0:
        raise ValueError("Insufficient stock")
    prod.stock_quantity = prod.stock_quantity - qty
    await session.flush()
    # If stock falls below low threshold, notify owner
    try:
        if prod.low_stock_threshold is not None and prod.stock_quantity <= prod.low_stock_threshold:
            # fetch store contact
            q = await session.execute(select(StoreModel).where(StoreModel.id == prod.store_id))
            store = q.scalar_one_or_none()
            if store and store.contact_whatsapp:
                await send_text(
                    store.contact_whatsapp,
                    f"Low stock alert: '{prod.name}' has {prod.stock_quantity} left.",
                )
    except Exception:
        pass
    return prod


async def increase_stock(session: AsyncSession, product_id: uuid.UUID, qty: int):
    q = select(Product).where(Product.id == product_id)
    res = await session.execute(q)
    prod = res.scalar_one_or_none()
    if not prod:
        return None
    prod.stock_quantity = prod.stock_quantity + qty
    await session.flush()
    return prod
