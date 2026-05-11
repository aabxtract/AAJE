import hashlib
import hmac
import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.intelligence.llm import categorize_transaction, translate_message
from app.intelligence.pii_scrubber import scrub
from app.intelligence.refinery import compute_score
from app.models.income_stream import IncomeStream
from app.models.transaction import Transaction
from app.models.user import User
from app.models.vault import Vault
from app.services.squad import transfer
from app.services.whatsapp_client import send_text
from app.utils.formatters import format_naira

logger = logging.getLogger(__name__)
router = APIRouter()


def _valid_signature(payload: bytes, signature: str) -> bool:
    if not signature:
        return False
    expected = hmac.new(settings.squad_secret_key.encode(), payload, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)


def _payload_value(payload: dict, *names, default=None):
    for name in names:
        if name in payload:
            return payload[name]
    data = payload.get("data", {})
    for name in names:
        if name in data:
            return data[name]
    return default


@router.post("/webhook/squad")
async def squad_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-squad-signature") or request.headers.get("squad-signature") or ""
    if not signature or not _valid_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid Squad signature")

    payload = await request.json()
    reference = _payload_value(payload, "transaction_ref", "transaction_reference", "reference", "ref")
    amount_kobo = _payload_value(payload, "amount", "transaction_amount", default=0)
    account_number = _payload_value(payload, "virtual_account_number", "account_number", "recipient_account")
    narration = _payload_value(payload, "narration", "remarks", "description", default="")
    tx_type = str(_payload_value(payload, "type", "transaction_type", default="credit")).lower()

    if not reference or not account_number:
        logger.info("Squad webhook missing reference or account number: %s", payload)
        return {"status": "ignored"}

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Transaction).where(Transaction.squad_transaction_ref == reference))
        if existing.scalar_one_or_none():
            return {"status": "duplicate"}

        stream_result = await db.execute(select(IncomeStream).where(IncomeStream.squad_account_number == str(account_number)))
        inbound_stream = stream_result.scalar_one_or_none()
        if not inbound_stream:
            logger.info("No stream found for Squad account %s", account_number)
            return {"status": "ignored"}

        user = await db.get(User, inbound_stream.user_id)
        streams_result = await db.execute(select(IncomeStream).where(IncomeStream.user_id == user.id))
        streams = streams_result.scalars().all()

        if "credit" not in tx_type or Decimal(str(amount_kobo)) <= 0:
            return {"status": "ignored"}

        amount = Decimal(str(amount_kobo)) / Decimal("100")
        selected_name = await categorize_transaction(
            scrub({"narration": narration, "full_name": user.full_name}).get("narration", narration),
            [stream.stream_name for stream in streams],
        )
        categorized_stream = next((stream for stream in streams if stream.stream_name == selected_name), inbound_stream)

        fee = Decimal("5")
        split_base = max(amount - fee, Decimal("0"))
        split_lines = []
        for stream in streams:
            split_amount = (split_base * Decimal(str(stream.split_percentage or 0)) / Decimal("100")).quantize(Decimal("0.01"))
            if split_amount <= 0:
                continue
            split_ref = f"SPLIT-{reference}-{str(stream.id)[:8]}"
            await transfer(float(split_amount), "000", stream.squad_account_number, stream.stream_name, "AAJE split", split_ref)
            vault_result = await db.execute(select(Vault).where(Vault.stream_id == stream.id))
            vault = vault_result.scalar_one_or_none()
            if vault:
                vault.current_balance = Decimal(vault.current_balance or 0) + split_amount
                vault.total_deposited = Decimal(vault.total_deposited or 0) + split_amount
            db.add(Transaction(
                user_id=user.id,
                stream_id=stream.id,
                amount=split_amount,
                type="credit",
                narration=f"Split from {reference}",
                category="split",
                source="squad_split",
                squad_transaction_ref=split_ref,
                timestamp=datetime.now(timezone.utc),
                processed=True,
            ))
            split_lines.append(f"{stream.stream_name}: {format_naira(float(split_amount))}")

        if fee > 0:
            await transfer(float(fee), settings.squad_revenue_bank_code, settings.squad_revenue_account, "AAJE Revenue", "AAJE fee", f"FEE-{reference}")

        db.add(Transaction(
            user_id=user.id,
            stream_id=categorized_stream.id,
            amount=amount,
            type="credit",
            narration=narration,
            category="inbound",
            source="squad",
            squad_transaction_ref=reference,
            timestamp=datetime.now(timezone.utc),
            processed=True,
        ))
        await db.commit()
        await compute_score(str(user.id), db)

    message = f"{format_naira(float(amount))} received. Here's how it was split:\n" + "\n".join(split_lines)
    message = await translate_message(message, user.preferred_language or "en")
    await send_text(user.whatsapp_no, message)
    return {"status": "processed"}
