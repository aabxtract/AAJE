import json
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.money import FailedTransfer, Supplier, Wallet
from app.models.transaction import Transaction
from app.models.user import User
from app.services.events import emit_event
from app.services.squad import transfer

router = APIRouter(prefix="/wallet", tags=["wallet"])


class WithdrawRequest(BaseModel):
    user_id: str
    amount: float
    pin_verified: bool = False
    bank_code: str | None = None
    account_number: str | None = None
    account_name: str | None = None


class SupplierRequest(BaseModel):
    user_id: str
    alias: str
    bank_name: str | None = None
    bank_code: str
    account_number: str


@router.get("/{user_id}")
async def get_wallet(user_id: str, db: AsyncSession = Depends(get_db)):
    wallet = await _ensure_wallet(db, user_id)
    return _wallet_payload(wallet)


@router.get("/{user_id}/transactions")
async def get_wallet_transactions(user_id: str, db: AsyncSession = Depends(get_db)):
    txs = (await db.execute(select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()))).scalars().all()
    return [
        {
            "id": str(tx.id),
            "amount": float(tx.amount or 0),
            "type": tx.type,
            "narration": tx.narration,
            "category": tx.category,
            "reference": tx.squad_transaction_ref,
            "status": tx.status,
            "source": tx.source,
            "created_at": tx.created_at,
        }
        for tx in txs
    ]


@router.post("/withdraw")
async def withdraw(payload: WithdrawRequest, db: AsyncSession = Depends(get_db)):
    if not payload.pin_verified:
        raise HTTPException(status_code=403, detail="PIN confirmation is required before withdrawal")
    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    wallet = await _ensure_wallet(db, payload.user_id)
    amount = Decimal(str(payload.amount))
    if Decimal(wallet.available_balance or 0) < amount:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")

    reference = f"WD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    bank_code = payload.bank_code or user.verified_bank_code
    account_number = payload.account_number or user.verified_bank_account
    account_name = payload.account_name or user.verified_bank_name or user.full_name
    if not bank_code or not account_number:
        raise HTTPException(status_code=400, detail="Withdrawal bank details are missing")

    try:
        provider_response = await transfer(float(amount), bank_code, account_number, account_name, "AAJE wallet withdrawal", reference)
    except Exception as exc:
        db.add(FailedTransfer(
            user_id=user.id,
            amount=amount,
            destination_json=json.dumps({"bank_code": bank_code, "account_number": account_number, "account_name": account_name}),
            reference=reference,
            error_message=str(exc),
        ))
        raise

    wallet.available_balance = Decimal(wallet.available_balance or 0) - amount
    wallet.total_withdrawn = Decimal(wallet.total_withdrawn or 0) + amount
    db.add(Transaction(
        user_id=user.id,
        amount=amount,
        type="debit",
        narration="AAJE wallet withdrawal",
        category="withdrawal",
        squad_transaction_ref=reference,
        status="success",
        source="withdrawal",
        provider="squad",
        raw_payload=json.dumps(provider_response),
        timestamp=datetime.now(timezone.utc),
        processed=True,
    ))
    await emit_event(db, {
        "event_type": "withdrawal_completed",
        "source": "wallet",
        "user_id": str(user.id),
        "amount": float(amount),
        "reference": reference,
    })
    return {"status": "success", "reference": reference, "wallet": _wallet_payload(wallet)}


@router.post("/suppliers")
async def create_supplier(payload: SupplierRequest, db: AsyncSession = Depends(get_db)):
    if not await db.get(User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    supplier = Supplier(
        user_id=payload.user_id,
        alias=payload.alias,
        bank_name=payload.bank_name,
        bank_code=payload.bank_code,
        account_number=payload.account_number,
    )
    db.add(supplier)
    await db.flush()
    return {"id": str(supplier.id), "alias": supplier.alias, "bank_name": supplier.bank_name, "bank_code": supplier.bank_code, "account_number": supplier.account_number}


async def _ensure_wallet(db: AsyncSession, user_id: str) -> Wallet:
    if not await db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    wallet = (await db.execute(select(Wallet).where(Wallet.user_id == user_id))).scalar_one_or_none()
    if wallet:
        return wallet
    wallet = Wallet(user_id=user_id)
    db.add(wallet)
    await db.flush()
    return wallet


def _wallet_payload(wallet: Wallet) -> dict:
    return {
        "id": str(wallet.id),
        "user_id": str(wallet.user_id),
        "available_balance": float(wallet.available_balance or 0),
        "total_earned": float(wallet.total_earned or 0),
        "total_withdrawn": float(wallet.total_withdrawn or 0),
        "last_updated": wallet.last_updated,
    }
