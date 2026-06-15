from __future__ import annotations

import logging
import re
import uuid as uuidlib
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.order import Order
from app.models.store import Store
from app.models.user import User
from app.redis import get_session, save_session
from app.services.whatsapp_client import send_text
from app.utils.formatters import format_naira

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "AAJE commands\n\n"
    "orders - see latest orders\n"
    "paid AAJE-XXXX - mark an order paid\n"
    "delivered AAJE-XXXX - mark a paid order delivered\n"
    "cancel AAJE-XXXX - cancel a pending order\n"
    "balance - paid sales total\n"
    "menu - show this list"
)

_ORDER_REF_GROUP = r"(AAJE-\d{4}-\d+)"


async def route_message(whatsapp_no: str, message: str, db: AsyncSession) -> None:
    message = (message or "").strip()
    if not message:
        return

    session = await get_session(whatsapp_no)
    user = await _load_user(db, session.get("user_id")) if session.get("user_id") else None
    if user is None:
        user = await _find_linked_user(db, whatsapp_no)
        if user is None:
            await _handle_unlinked(whatsapp_no)
            return
        session["user_id"] = str(user.id)
        session["stage"] = "ACTIVE"
        await save_session(whatsapp_no, session)

    lower = message.lower()
    if lower in {"menu", "help", "options", "/menu"}:
        await send_text(whatsapp_no, HELP_TEXT)
        return
    if lower == "orders":
        await _handle_list_orders(whatsapp_no, user, db)
        return
    if lower == "balance":
        await _handle_balance(whatsapp_no, user, db)
        return

    paid = re.match(rf"^(paid|confirm)\s+{_ORDER_REF_GROUP}\s*$", message, re.IGNORECASE)
    if paid:
        await _handle_status_command(
            whatsapp_no,
            user,
            paid.group(2).upper(),
            allowed={"pending"},
            new_status="paid",
            verb="marked paid",
            db=db,
        )
        return

    delivered = re.match(rf"^delivered\s+{_ORDER_REF_GROUP}\s*$", message, re.IGNORECASE)
    if delivered:
        await _handle_status_command(
            whatsapp_no,
            user,
            delivered.group(1).upper(),
            allowed={"paid"},
            new_status="delivered",
            verb="marked delivered",
            db=db,
        )
        return

    cancelled = re.match(rf"^(cancel|reject)\s+{_ORDER_REF_GROUP}\s*$", message, re.IGNORECASE)
    if cancelled:
        await _handle_status_command(
            whatsapp_no,
            user,
            cancelled.group(2).upper(),
            allowed={"pending"},
            new_status="cancelled",
            verb="cancelled",
            db=db,
        )
        return

    await send_text(whatsapp_no, HELP_TEXT)


async def _load_user(db: AsyncSession, user_id) -> User | None:
    if not user_id:
        return None
    try:
        return await db.get(User, uuidlib.UUID(str(user_id)))
    except (ValueError, TypeError):
        return None


async def _find_linked_user(db: AsyncSession, whatsapp_no: str) -> User | None:
    digits = "".join(ch for ch in (whatsapp_no or "") if ch.isdigit())
    if not digits:
        return None
    candidates = {digits}
    if digits.startswith("234") and len(digits) == 13:
        candidates.add("0" + digits[3:])
    rows = (await db.execute(select(User).where(User.whatsapp_no.in_(candidates)))).scalars().all()
    for user in rows:
        if user.whatsapp_connected:
            return user
    return None


async def _handle_unlinked(whatsapp_no: str) -> None:
    frontend = (settings.frontend_url or "https://aaje.store").rstrip("/")
    await send_text(
        whatsapp_no,
        "Welcome to AAJE. Create or connect your account first, then WhatsApp can send order and stock updates.\n\n"
        f"Start here: {frontend}/signup",
    )


async def _handle_list_orders(whatsapp_no: str, user: User, db: AsyncSession) -> None:
    store = await db.scalar(select(Store).where(Store.user_id == user.id))
    if not store:
        await send_text(whatsapp_no, "Complete your business setup first.")
        return

    orders = (
        await db.execute(
            select(Order)
            .where(Order.store_id == store.id)
            .order_by(Order.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    if not orders:
        await send_text(whatsapp_no, "No orders yet.")
        return

    lines = ["Latest orders:"]
    for order in orders:
        lines.append(
            f"{_status_badge(order.status)} {order.order_ref} - "
            f"{order.customer_name or 'Customer'} - "
            f"{format_naira(float(order.total_amount or 0))} - {order.status}"
        )
    await send_text(whatsapp_no, "\n".join(lines))


async def _handle_balance(whatsapp_no: str, user: User, db: AsyncSession) -> None:
    store = await db.scalar(select(Store).where(Store.user_id == user.id))
    if not store:
        await send_text(whatsapp_no, "Complete your business setup first.")
        return
    paid_orders = (
        await db.execute(
            select(Order).where(
                Order.store_id == store.id,
                Order.status.in_(["paid", "delivered"]),
            )
        )
    ).scalars().all()
    total = sum((Decimal(order.total_amount or 0) for order in paid_orders), Decimal(0))
    await send_text(
        whatsapp_no,
        f"Paid sales: {format_naira(float(total))}\nOrders paid: {len(paid_orders)}",
    )


async def _handle_status_command(
    whatsapp_no: str,
    user: User,
    order_ref: str,
    allowed: set[str],
    new_status: str,
    verb: str,
    db: AsyncSession,
) -> None:
    order = await db.scalar(select(Order).where(Order.order_ref == order_ref))
    if not order:
        await send_text(whatsapp_no, f"Order {order_ref} not found.")
        return
    store = await db.scalar(select(Store).where(Store.id == order.store_id))
    if not store or store.user_id != user.id:
        await send_text(whatsapp_no, f"Order {order_ref} not found.")
        return
    if order.status not in allowed:
        await send_text(whatsapp_no, f"Order {order_ref} is currently {order.status}.")
        return

    order.status = new_status
    order.payment_status = "paid" if new_status in {"paid", "delivered"} else "unpaid"
    await db.commit()
    await send_text(
        whatsapp_no,
        f"{order_ref} {verb}.\n"
        f"Customer: {order.customer_name or 'Customer'}\n"
        f"Amount: {format_naira(float(order.total_amount or 0))}",
    )


def _status_badge(status: str | None) -> str:
    return {
        "pending": "[pending]",
        "paid": "[paid]",
        "delivered": "[delivered]",
        "cancelled": "[cancelled]",
    }.get((status or "").lower(), "[order]")
