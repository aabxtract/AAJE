"""
Squad webhook — processes incoming payment notifications from Squad.

When a payment hits one of the trader's Squad virtual accounts:
  1. Validate the signature
  2. Deduplicate by transaction reference
  3. Match to a trader's income stream
  4. AI-categorize the payment narration
  5. Run the slicer to auto-split across vaults
  6. Recompute the trader's score
  7. Notify the trader via WhatsApp
"""
import hashlib
import hmac
import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.intelligence.llm import categorize_transaction
from app.intelligence.pii_scrubber import scrub
from app.intelligence.refinery import compute_score
from app.models.income_stream import IncomeStream
from app.models.transaction import Transaction
from app.models.user import User
from app.services.notifier import notify_anomaly, notify_split
from app.services.slicer import split_incoming_payment
from app.utils.formatters import format_naira

logger = logging.getLogger(__name__)
router = APIRouter()

# ₦10 flat deposit fee on every inbound credit
DEPOSIT_FEE = Decimal("10")

# Anomaly threshold — transactions above this trigger an alert
ANOMALY_THRESHOLD = Decimal("500000")


def _valid_signature(payload: bytes, signature: str) -> bool:
    """Verify Squad webhook HMAC-SHA512 signature."""
    if not signature:
        return False
    expected = hmac.new(
        settings.squad_secret_key.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _extract(payload: dict, *keys, default=None):
    """Extract a value from the payload, checking top level and nested data."""
    for key in keys:
        if key in payload:
            return payload[key]
    data = payload.get("data", {})
    for key in keys:
        if key in data:
            return data[key]
    return default


@router.post("/webhook/squad")
async def squad_webhook(request: Request):
    body = await request.body()
    signature = (
        request.headers.get("x-squad-signature")
        or request.headers.get("squad-signature")
        or ""
    )

    if not signature or not _valid_signature(body, signature):
        logger.warning("Squad webhook rejected: invalid signature")
        raise HTTPException(status_code=403, detail="Invalid Squad signature")

    payload = await request.json()
    logger.info("Squad webhook received: %s", {
        k: v for k, v in payload.items() if k != "data"
    })

    reference = _extract(
        payload, "transaction_ref", "transaction_reference", "reference", "ref"
    )
    amount_kobo = _extract(payload, "amount", "transaction_amount", default=0)
    account_number = _extract(
        payload, "virtual_account_number", "account_number", "recipient_account"
    )
    narration = _extract(payload, "narration", "remarks", "description", default="")
    tx_type = str(
        _extract(payload, "type", "transaction_type", default="credit")
    ).lower()

    if not reference or not account_number:
        logger.info("Squad webhook ignored: missing reference or account_number")
        return {"status": "ignored"}

    if "credit" not in tx_type:
        logger.info("Squad webhook ignored: not a credit transaction (type=%s)", tx_type)
        return {"status": "ignored"}

    if Decimal(str(amount_kobo)) <= 0:
        logger.info("Squad webhook ignored: zero or negative amount")
        return {"status": "ignored"}

    async with AsyncSessionLocal() as db:
        # 1. Deduplicate
        existing = await db.execute(
            select(Transaction).where(Transaction.squad_transaction_ref == reference)
        )
        if existing.scalar_one_or_none():
            logger.info("Squad webhook duplicate: %s", reference)
            return {"status": "duplicate"}

        # 2. Find the inbound stream
        stream_result = await db.execute(
            select(IncomeStream).where(
                IncomeStream.squad_account_number == str(account_number)
            )
        )
        inbound_stream = stream_result.scalar_one_or_none()
        if not inbound_stream:
            logger.info("No stream found for Squad account %s", account_number)
            return {"status": "ignored"}

        # 3. Load user
        user = await db.get(User, inbound_stream.user_id)
        if not user:
            logger.warning("No user found for stream %s", inbound_stream.id)
            return {"status": "ignored"}

        # 4. Convert from kobo to naira
        amount = Decimal(str(amount_kobo)) / Decimal("100")

        # 5. AI-categorize the narration
        streams_result = await db.execute(
            select(IncomeStream).where(IncomeStream.user_id == user.id)
        )
        all_streams = streams_result.scalars().all()
        stream_names = [s.stream_name for s in all_streams]

        scrubbed_narration = scrub({"narration": narration}).get("narration", narration)
        try:
            categorized_name = await categorize_transaction(scrubbed_narration, stream_names)
        except Exception:
            logger.exception("AI categorization failed, using inbound stream")
            categorized_name = inbound_stream.stream_name

        categorized_stream = next(
            (s for s in all_streams if s.stream_name == categorized_name),
            inbound_stream,
        )

        # 6. Record the master inbound transaction
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

        # 7. Run the slicer (no fee deduction — full amount is split)
        split_lines = await split_incoming_payment(
            user_id=user.id,
            inbound_stream=inbound_stream,
            amount=amount,
            reference=reference,
            narration=narration,
            db=db,
        )

        # 8. Charge ₦10 deposit fee to AAJE revenue account
        try:
            await transfer(
                float(DEPOSIT_FEE),
                settings.squad_revenue_bank_code,
                settings.squad_revenue_account,
                "AAJE Revenue",
                "AAJE deposit fee",
                f"FEE-{reference}",
            )
        except Exception:
            logger.exception("Deposit fee transfer failed for ref %s", reference)

        # 8. Recompute trader score
        try:
            await compute_score(str(user.id), db)
        except Exception:
            logger.exception("Score recomputation failed for user %s", user.id)

        await db.commit()

    # 9. Notify the trader via agent runtime
    from app.agents.agent_runtime import handle_event
    event_message = f"SYSTEM_EVENT: Received payment of {amount} NGN. Narration: '{narration}'. Transaction Ref: {reference}."
    try:
        await handle_event(user.whatsapp_no, event_message)
    except Exception:
        logger.exception("Agent runtime failed to process squad webhook event for user %s", user.id)

    logger.info(
        "Squad webhook processed via agent: %s",
        format_naira(float(amount)),
    )
    return {"status": "processed"}
