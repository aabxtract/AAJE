"""
Slicer — auto-splits incoming payments across a trader's vaults based on
their configured split percentages.

Flow:
  1. Incoming credit hits a Squad virtual account
  2. Slicer identifies the trader and their streams
  3. Deducts the AAJE fee (₦5 flat)
  4. Splits the remainder across all vaults by percentage
  5. Executes Squad-to-Squad internal transfers
  6. Updates vault balances and creates split transaction records
"""
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.income_stream import IncomeStream
from app.models.transaction import Transaction
from app.models.vault import Vault
from app.services.squad import transfer
from app.utils.formatters import format_naira

logger = logging.getLogger(__name__)



async def split_incoming_payment(
    user_id,
    inbound_stream: IncomeStream,
    amount: Decimal,
    reference: str,
    narration: str,
    db: AsyncSession,
) -> list[dict]:
    """Split an incoming payment across all of a trader's vaults.

    Returns:
        split_lines — a list of dicts with stream_name and amount for
        notification purposes.
    """
    # Load all streams for this user
    result = await db.execute(
        select(IncomeStream).where(IncomeStream.user_id == user_id)
    )
    streams = result.scalars().all()

    if not streams:
        logger.warning("No streams found for user %s during split", user_id)
        return []

    split_base = amount

    split_lines = []

    for stream in streams:
        percentage = Decimal(str(stream.split_percentage or 0))
        if percentage <= 0:
            continue

        split_amount = (split_base * percentage / Decimal("100")).quantize(Decimal("0.01"))
        if split_amount <= 0:
            continue

        split_ref = f"SPLIT-{reference}-{str(stream.id)[:8]}"

        # Execute Squad internal transfer if this isn't the inbound stream
        if str(stream.id) != str(inbound_stream.id) and stream.squad_account_number:
            try:
                await transfer(
                    float(split_amount),
                    "000",
                    stream.squad_account_number,
                    stream.stream_name,
                    "AAJE split",
                    split_ref,
                )
            except Exception:
                logger.exception(
                    "Split transfer failed for stream %s ref %s",
                    stream.stream_name, split_ref,
                )
                continue

        # Update vault balance
        vault_result = await db.execute(
            select(Vault).where(Vault.stream_id == stream.id)
        )
        vault = vault_result.scalar_one_or_none()
        if vault:
            vault.current_balance = Decimal(str(vault.current_balance or 0)) + split_amount
            vault.total_deposited = Decimal(str(vault.total_deposited or 0)) + split_amount

        # Record split transaction
        db.add(Transaction(
            user_id=user_id,
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

        split_lines.append({
            "stream_name": stream.stream_name,
            "amount": float(split_amount),
        })

    return split_lines
