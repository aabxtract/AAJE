import hashlib
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.bizprint import generate_bizprint
from app.intelligence.scorer import recalculate_user_score
from app.models.commerce import InventoryMovement, Order, OrderItem, Product, Store
from app.models.intelligence import Event, LedgerEntry
from app.models.money import Wallet
from app.models.notification_log import NotificationLog
from app.models.transaction import Transaction
from app.whatsapp.service import send_text

logger = logging.getLogger(__name__)


def _json_default(value):
    if isinstance(value, (datetime, UUID)):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


def build_idempotency_key(payload: dict) -> str:
    seed = json.dumps(payload, sort_keys=True, default=_json_default)
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


async def emit_event(db: AsyncSession, payload: dict, process_now: bool = True) -> Event:
    event_type = payload["event_type"]
    user_id = _coerce_uuid(payload["user_id"])
    source = payload.get("source", "system")
    store_id = _coerce_uuid(payload.get("store_id"))
    idempotency_key = payload.get("idempotency_key") or build_idempotency_key(payload)

    existing = await db.execute(select(Event).where(Event.idempotency_key == idempotency_key))
    event = existing.scalar_one_or_none()
    if event:
        return event

    event = Event(
        event_type=event_type,
        source=source,
        user_id=user_id,
        store_id=store_id,
        payload_json=payload,
        idempotency_key=idempotency_key,
    )
    db.add(event)
    await db.flush()
    if process_now:
        await process_event(db, event)
    return event


def _coerce_uuid(value):
    if value in {None, ""}:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


async def process_event(db: AsyncSession, event: Event) -> None:
    if event.processed:
        return
    payload = event.payload_json or {}
    event_type = event.event_type

    if event_type in {"payment_confirmed", "order_paid"}:
        await _record_payment_side_effects(db, event, payload)
    elif event_type in {
        "stock_added",
        "stock_removed",
        "inventory_reduced",
        "inventory_low",
        "product_updated",
        "store_created",
        "product_created",
        "order_created",
    }:
        await _refresh_intelligence(db, event.user_id, event.store_id)
    elif event_type in {"withdrawal_completed", "receipt_uploaded", "score_updated", "bizprint_generated"}:
        await _refresh_intelligence(db, event.user_id, event.store_id)

    event.processed = True


async def _record_payment_side_effects(db: AsyncSession, event: Event, payload: dict) -> None:
    reference = str(payload.get("reference") or payload.get("transaction_reference") or payload.get("order_id") or event.id)
    amount = Decimal(str(payload.get("amount") or 0))
    if amount <= 0:
        return

    tx_exists = await db.execute(select(Transaction).where(Transaction.squad_transaction_ref == reference))
    if not tx_exists.scalar_one_or_none():
        db.add(Transaction(
            user_id=event.user_id,
            store_id=event.store_id,
            amount=amount,
            type="credit",
            narration=payload.get("narration") or "Squad payment",
            category=payload.get("category") or "storefront_sale",
            source="squad",
            provider="squad",
            status="completed",
            squad_transaction_ref=reference,
            external_reference=payload.get("external_reference"),
            order_id=payload.get("order_id"),
            raw_payload=json.dumps(payload, default=_json_default),
            timestamp=datetime.now(timezone.utc),
            processed=True,
        ))
        db.add(LedgerEntry(
            user_id=event.user_id,
            store_id=event.store_id,
            direction="credit",
            amount=amount,
            reference=reference,
            source="squad",
        ))

    order_id = payload.get("order_id")
    if order_id:
        order = await db.get(Order, order_id)
        if order and order.payment_status != "paid":
            order.payment_status = "paid"
            order.order_status = "paid"
            order.status = "paid"
            order.squad_transaction_ref = reference
            order.paid_at = datetime.now(timezone.utc)
            await _reduce_inventory_for_order(db, order)
            await _notify_store_sale(db, order, amount, reference)

            if order.campaign_ref:
                from app.models.marketing import CampaignLink, CampaignConversion
                campaign = (await db.execute(
                    select(CampaignLink).where(
                        CampaignLink.store_id == order.store_id,
                        CampaignLink.ref_slug == order.campaign_ref,
                    )
                )).scalar_one_or_none()
                existing_conversion = (await db.execute(
                    select(CampaignConversion).where(CampaignConversion.order_id == order.id)
                )).scalar_one_or_none()
                if campaign and not existing_conversion:
                    db.add(CampaignConversion(
                        campaign_id=campaign.id,
                        order_id=order.id,
                        revenue=order.total_amount or amount
                    ))

    await _credit_wallet(db, event.user_id, amount)
    await _refresh_intelligence(db, event.user_id, event.store_id)


async def _reduce_inventory_for_order(db: AsyncSession, order: Order) -> None:
    items = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    for item in items.scalars().all():
        product = await db.get(Product, item.product_id)
        if not product:
            continue
        product.stock_quantity = max((product.stock_quantity or 0) - item.quantity, 0)
        db.add(InventoryMovement(
            store_id=order.store_id,
            product_id=product.id,
            movement_type="out",
            quantity=item.quantity,
            reason="order_paid",
            related_order_id=order.id,
        ))
        await emit_event(db, {
            "event_type": "inventory_reduced",
            "source": "squad_intelligence",
            "user_id": str(order.user_id),
            "store_id": str(order.store_id),
            "order_id": str(order.id),
            "product_id": str(product.id),
            "quantity": item.quantity,
            "metadata": {"product_name": product.name, "stock_quantity": product.stock_quantity},
        }, process_now=False)
        if product.stock_quantity <= (product.low_stock_threshold or 0):
            await emit_event(db, {
                "event_type": "inventory_low",
                "source": "squad_intelligence",
                "user_id": str(order.user_id),
                "store_id": str(order.store_id),
                "product_id": str(product.id),
                "metadata": {"product_name": product.name, "stock_quantity": product.stock_quantity},
            }, process_now=False)


async def _refresh_intelligence(db: AsyncSession, user_id, store_id=None) -> None:
    await recalculate_user_score(db, user_id)
    snapshot = await generate_bizprint(db, user_id, store_id)
    await emit_event(db, {
        "event_type": "bizprint_generated",
        "source": "squad_intelligence",
        "user_id": str(user_id),
        "store_id": str(store_id) if store_id else None,
        "bizprint_snapshot_id": str(snapshot.id),
        "metadata": {"data_quality": snapshot.data_quality},
    }, process_now=False)


async def _credit_wallet(db: AsyncSession, user_id, amount: Decimal) -> Wallet:
    wallet = (await db.execute(select(Wallet).where(Wallet.user_id == user_id))).scalar_one_or_none()
    if not wallet:
        wallet = Wallet(user_id=user_id)
        db.add(wallet)
        await db.flush()
    wallet.available_balance = Decimal(wallet.available_balance or 0) + amount
    wallet.total_earned = Decimal(wallet.total_earned or 0) + amount
    return wallet


async def _notify_store_sale(db: AsyncSession, order: Order, amount: Decimal, reference: str) -> None:
    store = await db.get(Store, order.store_id)
    if not store or not store.contact_whatsapp:
        return
    message = (
        f"New paid storefront order - {store.store_name}\n"
        f"Order: {str(order.id)[:8]}\n"
        f"Amount: NGN {float(amount):,.2f}\n"
        f"Status: paid. Inventory has been updated.\n"
        f"Ref: {reference}"
    )
    db.add(NotificationLog(
        user_id=order.user_id,
        notification_type="store_sale",
        message=message,
        channel="whatsapp",
        status="queued",
    ))
    try:
        await send_text(store.contact_whatsapp, message)
    except Exception:
        logger.exception("Failed to send storefront sale notification for order %s", order.id)
