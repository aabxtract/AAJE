"""Agent tools — CLAUDE.md §8.

Five tools exposed to the LLM for MVP. The LLM (call 1) selects one; the
backend executes it; the result is fed back into LLM call 2 for response
generation.

``add_product`` and ``initiate_withdrawal`` are kept dispatchable (in case
the keyword fallback routes there) but intentionally NOT in
``TOOL_DEFINITIONS`` — so the LLM doesn't offer features the MVP doesn't
have. They return a "coming soon" payload instead of touching the DB.

Every tool returns a structured dict that is JSON-serialisable. Tools NEVER
raise out — they catch and return ``{"error": "..."}``. The agent loop relies
on this contract.
"""
from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.bizprint import BizPrint
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.store import Store
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet

logger = logging.getLogger(__name__)


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_store_summary",
            "description": (
                "Get today's snapshot for the trader's store: today's order count, "
                "today's revenue, pending orders count, and top-selling product. "
                "Call when the trader asks how their business is going, summary, performance."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_wallet_balance",
            "description": (
                "Get trader's wallet: available_balance, total_earned, recent transactions. "
                "Call when trader asks about money, balance, earnings, wallet."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_orders",
            "description": (
                "List trader's orders. Call when trader wants to see their orders. "
                "Filter by status if specified."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": [
                            "pending",
                            "transfer_claimed",
                            "confirmed",
                            "rejected",
                            "delivered",
                            "cancelled",
                            "all",
                        ],
                        "description": "Order status filter. Default 'all'.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max orders to return. Default 5.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_bizprint",
            "description": (
                "Get trader's BizPrint financial identity score: score, grade, "
                "component breakdown, loan eligibility ceiling. "
                "Call when trader asks about BizPrint, credit, score, loan eligibility."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_store_link",
            "description": (
                "Return the trader's public storefront URL for sharing with customers."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


async def execute_tool(
    name: str, arguments: dict, *, db: AsyncSession, user: User
) -> dict:
    """Dispatch a tool by name. Always returns a dict, never raises."""
    try:
        if name == "get_store_summary":
            return await _get_store_summary(db, user)
        if name == "get_wallet_balance":
            return await _get_wallet_balance(db, user)
        if name == "get_orders":
            return await _get_orders(
                db, user,
                status=arguments.get("status") or "all",
                limit=int(arguments.get("limit") or 5),
            )
        if name == "add_product":
            return await _add_product(
                db, user,
                name=str(arguments.get("name") or "").strip(),
                price=arguments.get("price"),
                category=arguments.get("category"),
            )
        if name == "get_bizprint":
            return await _get_bizprint(db, user)
        if name == "initiate_withdrawal":
            return await _initiate_withdrawal(
                db, user, amount=arguments.get("amount"),
            )
        if name == "get_store_link":
            return await _get_store_link(db, user)
        return {"error": f"Unknown tool: {name}"}
    except Exception:
        logger.exception("Tool %s failed", name)
        return {"error": "Tool execution failed", "tool": name}


async def _get_store(db: AsyncSession, user: User) -> Store | None:
    return (
        await db.execute(select(Store).where(Store.user_id == user.id))
    ).scalar_one_or_none()


async def _get_store_summary(db: AsyncSession, user: User) -> dict:
    store = await _get_store(db, user)
    if not store:
        return {"error": "no_store", "message": "Trader has no store yet"}

    from datetime import date

    today_orders = (
        await db.scalar(
            select(func.count(Order.id)).where(
                Order.store_id == store.id,
                func.date(Order.created_at) == date.today(),
            )
        )
    ) or 0
    today_revenue = (
        await db.scalar(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.store_id == store.id,
                Order.payment_status == "paid",
                func.date(Order.created_at) == date.today(),
            )
        )
    ) or 0
    pending = (
        await db.scalar(
            select(func.count(Order.id)).where(
                Order.store_id == store.id, Order.status == "pending"
            )
        )
    ) or 0

    top_row = (
        await db.execute(
            select(
                OrderItem.product_name,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("qty"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.store_id == store.id, Order.payment_status == "paid")
            .group_by(OrderItem.product_name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(1)
        )
    ).first()
    top_product = top_row[0] if top_row else None

    return {
        "today_orders": int(today_orders),
        "today_revenue": float(today_revenue),
        "pending_orders": int(pending),
        "top_product": top_product,
        "store_name": store.store_name,
    }


async def _get_wallet_balance(db: AsyncSession, user: User) -> dict:
    wallet = (
        await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    ).scalar_one_or_none()
    if not wallet:
        return {
            "available_balance": 0.0,
            "total_earned": 0.0,
            "total_orders_paid": 0,
            "recent_transactions": [],
        }

    recent = (
        await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    return {
        "available_balance": float(wallet.available_balance or 0),
        "total_earned": float(wallet.total_earned or 0),
        "total_orders_paid": int(wallet.total_orders_paid or 0),
        "recent_transactions": [
            {
                "amount": float(t.amount or 0),
                "type": t.type,
                "narration": t.narration,
                "status": t.status,
            }
            for t in recent
        ],
    }


async def _get_orders(
    db: AsyncSession, user: User, *, status: str, limit: int
) -> dict:
    store = await _get_store(db, user)
    if not store:
        return {"orders": [], "total": 0, "store_missing": True}

    where = [Order.store_id == store.id]
    if status and status != "all":
        where.append(Order.status == status)

    rows = (
        await db.execute(
            select(Order)
            .where(*where)
            .order_by(Order.created_at.desc())
            .limit(max(1, min(limit, 10)))
        )
    ).scalars().all()

    return {
        "filter_status": status,
        "count": len(rows),
        "orders": [
            {
                "order_ref": o.order_ref,
                "customer_name": o.customer_name or "Guest",
                "amount": float(o.total_amount or 0),
                "status": o.status,
                "payment_status": o.payment_status,
            }
            for o in rows
        ],
    }


async def _add_product(
    db: AsyncSession,
    user: User,
    *,
    name: str,
    price: Any,
    category: str | None = None,
) -> dict:
    """MVP: chat-based product creation is deferred — dashboard only.

    Kept as a dispatchable stub because ``_keyword_fallback`` still routes
    'add X 1000' messages here. Returns a structured "coming soon" payload
    so LLM Call 2 can generate a polite redirect to the dashboard.
    """
    return {
        "ok": False,
        "deferred": True,
        "message": (
            "Adding products from chat is coming soon. For now, add products "
            "in your AAJE dashboard at aaje.store/admin/products."
        ),
        "attempted_name": name or None,
    }


async def _get_bizprint(db: AsyncSession, user: User) -> dict:
    bp = (
        await db.execute(
            select(BizPrint)
            .where(BizPrint.user_id == user.id)
            .order_by(BizPrint.computed_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not bp:
        return {
            "available": False,
            "message": (
                "BizPrint not yet computed. Process at least one paid order, "
                "then check back."
            ),
        }
    return {
        "available": True,
        "score": float(bp.trader_score or 0),
        "grade": bp.credit_grade or "—",
        "consistency": float(bp.consistency_score or 0),
        "volume": float(bp.volume_score or 0),
        "growth": float(bp.growth_score or 0),
        "tenure": float(bp.tenure_score or 0),
        "loan_ceiling": float(bp.recommended_loan_ceiling or 0),
        "orders_analyzed": int(bp.total_orders_analyzed or 0),
    }


async def _initiate_withdrawal(
    db: AsyncSession, user: User, *, amount: Any = None
) -> dict:
    """MVP: there is no withdrawal flow. Customers pay direct to the
    trader's bank account via the manual-transfer flow, so the trader's
    money is already on their bank account — no AAJE wallet to withdraw
    from. Returns a structured "no withdrawal needed" payload.
    """
    return {
        "ok": False,
        "deferred": True,
        "message": (
            "There's no AAJE wallet to withdraw from right now — customers "
            "transfer directly to your bank account, so your money is "
            "already with you. Reply *balance* to see confirmed sales this "
            "month. Wallet withdrawals come back once AAJE adds automated "
            "payments next month."
        ),
    }


async def _get_store_link(db: AsyncSession, user: User) -> dict:
    store = await _get_store(db, user)
    if not store:
        return {"error": "no_store", "message": "Set up your store first"}
    from app.utils.formatters import build_store_url

    url = build_store_url(store.store_slug)
    return {
        "store_name": store.store_name,
        "url": url,
        "is_published": bool(store.is_published),
        "share_message": f"Shop with me on AAJE — {store.store_name}: {url}",
    }
