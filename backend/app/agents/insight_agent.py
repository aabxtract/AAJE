"""
Insight agent — generates contextual financial debriefs and daily summaries.

Uses the full pipeline:  scrub → refinery → LLM → translate → send.
"""
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.intelligence.llm import generate_insight, translate_message
from app.intelligence.refinery import compute_score
from app.models.income_stream import IncomeStream
from app.models.transaction import Transaction
from app.models.user import User
from app.models.vault import Vault
from app.services.whatsapp_client import send_text
from app.utils.formatters import format_naira
from app.utils.pii_scrubber import scrub

logger = logging.getLogger(__name__)


async def handle_debrief(whatsapp_no: str, session: dict):
    """Generate a daily debrief for the trader."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
        user = result.scalar_one_or_none()
        if not user:
            await send_text(whatsapp_no, "I could not find your AAJE account.")
            return

        # Fetch today's transactions
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        tx_result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .where(Transaction.timestamp >= start_of_day)
        )
        today_txns = tx_result.scalars().all()

        # Fetch vault balances
        vault_result = await db.execute(
            select(IncomeStream, Vault)
            .join(Vault, Vault.stream_id == IncomeStream.id)
            .where(IncomeStream.user_id == user.id)
        )
        vault_rows = vault_result.all()

        # Compute score
        score_data = await compute_score(str(user.id), db)

    # Build debrief
    total_in = sum(float(tx.amount) for tx in today_txns if tx.type == "credit")
    total_out = sum(float(tx.amount) for tx in today_txns if tx.type == "debit")
    tx_count = len(today_txns)

    vault_lines = []
    total_balance = Decimal("0")
    for stream, vault in vault_rows:
        balance = vault.current_balance or Decimal("0")
        total_balance += balance
        vault_lines.append(f"  • {stream.stream_name}: {format_naira(float(balance))}")

    debrief_parts = [
        f"📊 *Daily Debrief* — {now.strftime('%d %b %Y')}",
        "",
        f"Today: {tx_count} transactions",
        f"  💰 In: {format_naira(total_in)}",
        f"  💸 Out: {format_naira(total_out)}",
        f"  📈 Net: {format_naira(total_in - total_out)}",
        "",
        "Vault Balances:",
        *vault_lines,
        f"  *Total: {format_naira(float(total_balance))}*",
        "",
        f"Trader Score: {score_data.get('trader_score', 0)}/100 ({score_data.get('credit_grade', 'D')})",
    ]

    # Add LLM insight if there are transactions
    if today_txns:
        scrubbed = scrub({
            "transactions": [
                {"amount": float(tx.amount), "type": tx.type, "category": tx.category}
                for tx in today_txns
            ],
            "total_balance": float(total_balance),
            "score": score_data.get("trader_score", 0),
        })
        ai_tip = await generate_insight(scrubbed)
        debrief_parts.extend(["", f"💡 {ai_tip}"])

    message = "\n".join(debrief_parts)
    message = await translate_message(message, session.get("language", "en"))
    await send_text(whatsapp_no, message)


async def send_daily_debrief_to_all():
    """Called by the scheduler to send debriefs to all active traders."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.onboarding_complete == True)
        )
        users = result.scalars().all()

    for user in users:
        try:
            session = {"language": user.preferred_language or "en"}
            await handle_debrief(user.whatsapp_no, session)
        except Exception:
            logger.exception("Failed to send debrief to %s", user.whatsapp_no)
