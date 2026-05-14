import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models.commerce import Order, Store
from app.models.transaction import Transaction
from app.events.handlers import emit_event
from app.payments.squad import get_transfer_status, transfer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments"])
DEPOSIT_FEE = Decimal("10")


class InitiatePaymentRequest(BaseModel):
    order_id: str


class WithdrawRequest(BaseModel):
    user_id: str
    amount: float
    bank_code: str
    account_number: str
    account_name: str
    pin_verified: bool = False
    narration: str = "AAJE withdrawal"


@router.post("/initiate")
async def initiate_payment(payload: InitiatePaymentRequest, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, payload.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    store = await db.get(Store, order.store_id)
    return {
        "order_id": str(order.id),
        "reference": order.squad_payment_reference,
        "amount": float(order.total_amount or 0),
        "currency": "NGN",
        "payment_channel": "squad_virtual_account",
        "virtual_account_number": store.squad_virtual_account_number if store else None,
        "status": order.payment_status,
    }


@router.post("/withdraw")
async def withdraw(payload: WithdrawRequest, db: AsyncSession = Depends(get_db)):
    if not payload.pin_verified:
        raise HTTPException(status_code=403, detail="PIN confirmation is required before withdrawal")
    reference = f"WD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    result = await transfer(
        payload.amount,
        payload.bank_code,
        payload.account_number,
        payload.account_name,
        payload.narration,
        reference,
    )
    db.add(Transaction(
        user_id=payload.user_id,
        amount=Decimal(str(payload.amount)),
        type="debit",
        narration=payload.narration,
        category="withdrawal",
        source="squad",
        provider="squad",
        status="completed",
        squad_transaction_ref=reference,
        raw_payload=json.dumps(result),
        timestamp=datetime.now(timezone.utc),
        processed=True,
    ))
    await emit_event(db, {
        "event_type": "withdrawal_completed",
        "source": "squad",
        "user_id": payload.user_id,
        "amount": payload.amount,
        "reference": reference,
    })
    return {"status": "processed", "reference": reference, "provider_response": result}


@router.post("/webhook/squad")
async def squad_payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    data = payload.get("data") or payload
    reference = data.get("transaction_ref") or data.get("transaction_reference") or data.get("reference")
    amount_raw = data.get("amount") or data.get("transaction_amount") or 0
    account_number = data.get("virtual_account_number") or data.get("account_number") or data.get("recipient_account")
    if not reference:
        return {"status": "ignored", "reason": "missing_reference"}

    existing = await db.execute(select(Transaction).where(Transaction.squad_transaction_ref == reference))
    if existing.scalar_one_or_none():
        return {"status": "duplicate"}

    order = (await db.execute(select(Order).where(Order.squad_payment_reference == reference))).scalar_one_or_none()
    store = None
    if order:
        store = await db.get(Store, order.store_id)
    elif account_number:
        store = (await db.execute(select(Store).where(Store.squad_virtual_account_number == str(account_number)))).scalar_one_or_none()

    if not store:
        logger.info("Squad payment webhook ignored; no AAJE store for reference=%s account=%s", reference, account_number)
        return {"status": "ignored", "reason": "store_not_found"}

    gross_amount = Decimal(str(amount_raw))
    if gross_amount > 1000000:
        gross_amount = gross_amount / Decimal("100")
    fee = DEPOSIT_FEE if gross_amount > DEPOSIT_FEE else Decimal("0")
    net_amount = gross_amount - fee

    if fee:
        try:
            await transfer(
                float(fee),
                settings.squad_revenue_bank_code,
                settings.squad_revenue_account,
                "AAJE Revenue",
                "AAJE storefront payment fee",
                f"FEE-{reference}",
            )
        except Exception:
            logger.exception("AAJE payment fee transfer failed for reference %s", reference)

    event = await emit_event(db, {
        "event_type": "payment_confirmed",
        "source": "squad",
        "user_id": str(store.user_id),
        "store_id": str(store.id),
        "order_id": str(order.id) if order else None,
        "amount": float(net_amount),
        "reference": reference,
        "metadata": {**data, "gross_amount": float(gross_amount), "aaje_fee": float(fee), "net_amount": float(net_amount)},
        "idempotency_key": f"squad:{reference}",
    })
    return {"status": "processed", "event_id": str(event.id)}


@router.get("/verify/{reference}")
async def verify_payment(reference: str, db: AsyncSession = Depends(get_db)):
    tx = (await db.execute(select(Transaction).where(Transaction.squad_transaction_ref == reference))).scalar_one_or_none()
    if tx:
        return {"reference": reference, "status": tx.status, "amount": float(tx.amount)}
    return {"reference": reference, "status": "not_found", "provider": await get_transfer_status(reference)}
