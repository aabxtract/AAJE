from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.notification_log import NotificationLog
from app.models.order import Order
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet
from app.services.whatsapp_client import send_text
from app.utils.formatters import format_naira

logger = logging.getLogger(__name__)
router = APIRouter(tags=["monnify"])


@router.post("/webhook/monnify")
async def receive_monnify_webhook(
    request: Request,
    background: BackgroundTasks,
    monnify_signature: Annotated[Optional[str], Header(alias="monnify-signature")] = None,
):
    """Monnify payment notification.

    Returns 200 only after successful processing (or confirmed dedupe).
    Returns 403 on signature failure, 500 on processing failure so Monnify
    will retry per CLAUDE.md §10.
    """
    raw_body = await request.body()

    # Signature validation — fail closed in non-dev when secret is set
    if settings.app_env != "development":
        if not settings.monnify_secret_key:
            logger.error("MONNIFY_SECRET_KEY missing in non-dev environment")
            raise HTTPException(status_code=503, detail="Webhook not configured")
        if not monnify_signature or not _valid_signature(raw_body, monnify_signature):
            logger.warning("Monnify webhook: invalid signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
    elif settings.monnify_secret_key:
        if not monnify_signature or not _valid_signature(raw_body, monnify_signature):
            logger.warning("Monnify webhook: invalid signature (dev)")
            raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError:
        logger.error("Monnify webhook: malformed JSON")
        raise HTTPException(status_code=400, detail="Malformed JSON")

    event_type = payload.get("eventType") or ""
    event_data = payload.get("eventData") or {}

    # Only react to successful transactions. Other event types (e.g. settlement)
    # are acknowledged with 200 but not processed.
    if event_type and event_type != "SUCCESSFUL_TRANSACTION":
        logger.info("Monnify webhook: ignoring event %s", event_type)
        return Response(status_code=200)

    payment_reference = event_data.get("paymentReference") or payload.get("paymentReference")
    transaction_reference = (
        event_data.get("transactionReference") or payload.get("transactionReference")
    )
    payment_status = (
        event_data.get("paymentStatus") or payload.get("paymentStatus") or ""
    ).upper()
    amount_paid = event_data.get("amountPaid") or payload.get("amountPaid") or 0

    if not payment_reference or not transaction_reference:
        logger.warning("Monnify webhook: missing references — payload=%s", str(payload)[:300])
        return Response(status_code=200)

    if payment_status != "PAID":
        logger.info(
            "Monnify webhook: status=%s for %s — not processing",
            payment_status, payment_reference,
        )
        return Response(status_code=200)

    try:
        result = await _process_paid_transaction(
            payment_reference=payment_reference,
            transaction_reference=transaction_reference,
            amount_paid=Decimal(str(amount_paid)),
        )
    except Exception:
        logger.exception(
            "Monnify webhook processing failed for %s — Monnify will retry",
            payment_reference,
        )
        # Return 500 so Monnify retries automatically. Per CLAUDE.md §10.
        raise HTTPException(status_code=500, detail="Processing failed")

    if result and result.get("order_id"):
        background.add_task(_notify_trader_paid, result["order_id"])

    return Response(status_code=200)


async def _process_paid_transaction(
    payment_reference: str,
    transaction_reference: str,
    amount_paid: Decimal,
) -> dict | None:
    """Atomic update: order → wallet → transaction row.

    Returns ``{"order_id": str}`` on success, ``None`` on dedupe or not-found.
    Raises on DB failure — caller turns this into a 500 for Monnify retry.
    """
    async with AsyncSessionLocal() as db:
        # Dedupe — CLAUDE.md §18 rule 7
        existing = await db.execute(
            select(Transaction).where(Transaction.monnify_ref == transaction_reference)
        )
        if existing.scalar_one_or_none() is not None:
            logger.info(
                "Monnify webhook: %s already processed (dedupe)",
                transaction_reference,
            )
            return None

        order = (
            await db.execute(select(Order).where(Order.order_ref == payment_reference))
        ).scalar_one_or_none()
        if not order:
            logger.warning(
                "Monnify webhook: no order found for paymentReference=%s",
                payment_reference,
            )
            return None

        order_total = Decimal(str(order.total_amount or 0))
        if abs(amount_paid - order_total) > Decimal("0.01"):
            # Amount mismatch — log critical, do NOT update wallet automatically
            logger.error(
                "Monnify amount mismatch for %s: expected %s got %s",
                payment_reference, order_total, amount_paid,
            )
            db.add(NotificationLog(
                user_id=order.user_id,
                type="payment_amount_mismatch",
                content=(
                    f"Order {payment_reference}: expected {order_total} but received "
                    f"{amount_paid}. Manual review required."
                ),
                delivered=False,
            ))
            await db.commit()
            return None

        # Per CLAUDE.md §18 rule 15: zero platform fee for MVP
        fee = Decimal("0")
        net_amount = amount_paid - fee

        order.payment_status = "paid"
        if order.status == "pending":
            order.status = "processing"
        order.monnify_transaction_ref = transaction_reference

        wallet = (
            await db.execute(select(Wallet).where(Wallet.user_id == order.user_id))
        ).scalar_one_or_none()
        if wallet is None:
            wallet = Wallet(user_id=order.user_id)
            db.add(wallet)
            await db.flush()

        wallet.available_balance = (
            Decimal(str(wallet.available_balance or 0)) + net_amount
        )
        wallet.total_earned = (
            Decimal(str(wallet.total_earned or 0)) + amount_paid
        )
        wallet.total_orders_paid = int(wallet.total_orders_paid or 0) + 1

        db.add(Transaction(
            user_id=order.user_id,
            order_id=order.id,
            amount=amount_paid,
            fee=fee,
            net_amount=net_amount,
            type="order_payment",
            narration=f"Payment for order {payment_reference}",
            monnify_ref=transaction_reference,
            status="success",
        ))

        await db.commit()
        return {"order_id": str(order.id)}


def _valid_signature(raw_body: bytes, signature: str) -> bool:
    """Monnify signs with HMAC-SHA512 of raw body using secret_key."""
    expected = hmac.new(
        settings.monnify_secret_key.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature.lower())


async def _notify_trader_paid(order_id: str) -> None:
    """BackgroundTask: WhatsApp the trader when payment confirms.

    Best-effort. Logs to notification_log so failures are observable.
    """
    try:
        async with AsyncSessionLocal() as db:
            order = await db.get(Order, uuid.UUID(order_id))
            if not order:
                return
            user = await db.get(User, order.user_id)
            content = (
                f"💰 New order paid!\n\n"
                f"Order: {order.order_ref}\n"
                f"Customer: {order.customer_name or 'Guest'}\n"
                f"Amount: {format_naira(float(order.total_amount or 0))}\n\n"
                f"Reply 'orders' to see details."
            )
            delivered = False
            if user and user.whatsapp_connected and user.whatsapp_no:
                try:
                    await send_text(user.whatsapp_no, content)
                    delivered = True
                except Exception:
                    logger.exception(
                        "Failed to deliver payment notification for %s",
                        order.order_ref,
                    )
            db.add(NotificationLog(
                user_id=order.user_id,
                type="payment_confirmed",
                content=content,
                delivered=delivered,
            ))
            await db.commit()
    except Exception:
        logger.exception("Failed to log payment notification for %s", order_id)
