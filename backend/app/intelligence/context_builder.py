"""Trader context for the WhatsApp agent.

Builds a clean dict from the database that LLM Call 2 consumes to generate
a personalized response. Run pii_scrubber.scrub() on the result before
passing to the LLM (CLAUDE.md §13, §18 rule 10).
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.bizprint import BizPrint
from app.models.order import Order
from app.models.product import Product
from app.models.store import Store
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet

logger = logging.getLogger(__name__)


async def build_context(db: AsyncSession, user: User) -> dict:
    """Build the trader context dict.

    Returns a dict shaped for the system prompt's ``{scrubbed_context}`` slot.
    Falls back to a minimal dict on DB error so the agent can still respond.
    """
    try:
        return await _build(db, user)
    except Exception:
        logger.exception("Context build failed; returning minimal context")
        return _minimal_context(user)


async def _build(db: AsyncSession, user: User) -> dict:
    store = (
        await db.execute(select(Store).where(Store.user_id == user.id))
    ).scalar_one_or_none()

    wallet = (
        await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    ).scalar_one_or_none()

    bizprint = (
        await db.execute(
            select(BizPrint)
            .where(BizPrint.user_id == user.id)
            .order_by(BizPrint.computed_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    product_count = 0
    pending_orders = 0
    today_revenue = Decimal("0")
    recent_orders: list[dict] = []

    if store:
        product_count = (
            await db.scalar(
                select(func.count(Product.id)).where(
                    Product.store_id == store.id, Product.is_available.is_(True)
                )
            )
        ) or 0

        pending_orders = (
            await db.scalar(
                select(func.count(Order.id)).where(
                    Order.store_id == store.id, Order.status == "pending"
                )
            )
        ) or 0

        today_revenue = Decimal(
            str(
                (
                    await db.scalar(
                        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                            Order.store_id == store.id,
                            Order.payment_status == "paid",
                            func.date(Order.created_at) == date.today(),
                        )
                    )
                )
                or 0
            )
        )

        recent_order_rows = (
            await db.execute(
                select(Order)
                .where(Order.store_id == store.id)
                .order_by(Order.created_at.desc())
                .limit(5)
            )
        ).scalars().all()
        recent_orders = [
            {
                "order_ref": o.order_ref,
                "customer_name": o.customer_name,
                "amount": float(o.total_amount or 0),
                "status": o.status,
                "payment_status": o.payment_status,
            }
            for o in recent_order_rows
        ]

    from app.utils.formatters import build_store_url

    return {
        "trader": {
            "full_name": user.full_name,  # scrubbed to first name later
            "language": user.preferred_language or "en",
            "onboarding_complete": bool(user.onboarding_complete),
        },
        "store": (
            {
                "name": store.store_name,
                "slug": store.store_slug,
                "public_url": build_store_url(store.store_slug),
                "is_published": bool(store.is_published),
                "product_count": int(product_count),
            }
            if store
            else None
        ),
        "wallet": (
            {
                "available_balance": float(wallet.available_balance or 0),
                "total_earned": float(wallet.total_earned or 0),
                "total_orders_paid": int(wallet.total_orders_paid or 0),
            }
            if wallet
            else {"available_balance": 0, "total_earned": 0, "total_orders_paid": 0}
        ),
        "today": {
            "revenue": float(today_revenue),
            "pending_orders": int(pending_orders),
        },
        "recent_orders": recent_orders,
        "bizprint": (
            {
                "score": float(bizprint.trader_score or 0),
                "grade": bizprint.credit_grade or "—",
                "loan_ceiling": float(bizprint.recommended_loan_ceiling or 0),
            }
            if bizprint
            else None
        ),
    }


def _minimal_context(user: User) -> dict:
    return {
        "trader": {
            "full_name": user.full_name or "",
            "language": user.preferred_language or "en",
            "onboarding_complete": bool(user.onboarding_complete),
        },
        "store": None,
        "wallet": {"available_balance": 0, "total_earned": 0, "total_orders_paid": 0},
        "today": {"revenue": 0, "pending_orders": 0},
        "recent_orders": [],
        "bizprint": None,
    }
