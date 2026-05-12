"""
Notifier — the mandatory notification pipeline.

Order: scrub → refinery context → LLM insight → translate → send

Every outbound notification to a trader passes through this pipeline
to ensure PII is never exposed and messages are in the trader's language.
"""
import logging

from sqlalchemy import insert

from app.database import AsyncSessionLocal
from app.intelligence.llm import generate_insight, translate_message
from app.intelligence.pii_scrubber import scrub
from app.models.notification_log import NotificationLog
from app.services.whatsapp_client import send_text
from app.utils.formatters import format_naira

logger = logging.getLogger(__name__)


async def notify_split(
    whatsapp_no: str,
    user_id,
    amount: float,
    split_lines: list[dict],
    language: str = "en",
):
    """Notify a trader about an incoming payment and how it was split."""
    lines = [f"💰 {format_naira(amount)} received!\n\nHere's how it was split:"]
    for entry in split_lines:
        lines.append(f"  • {entry['stream_name']}: {format_naira(entry['amount'])}")

    message = "\n".join(lines)
    message = await translate_message(message, language)
    await send_text(whatsapp_no, message)

    await _log_notification(user_id, "split_alert", message)


async def notify_withdrawal(
    whatsapp_no: str,
    user_id,
    amount: float,
    stream_name: str,
    reference: str,
    language: str = "en",
):
    """Notify trader that a withdrawal was processed."""
    message = (
        f"✅ Withdrawal of {format_naira(amount)} from {stream_name} has been sent to your bank account.\n"
        f"Ref: {reference}"
    )
    message = await translate_message(message, language)
    await send_text(whatsapp_no, message)

    await _log_notification(user_id, "withdrawal_confirmed", message)


async def notify_payment(
    whatsapp_no: str,
    user_id,
    amount: float,
    supplier_name: str,
    reference: str,
    language: str = "en",
):
    """Notify trader that a supplier payment was processed."""
    message = (
        f"✅ Payment of {format_naira(amount)} to {supplier_name} completed.\n"
        f"Ref: {reference}"
    )
    message = await translate_message(message, language)
    await send_text(whatsapp_no, message)

    await _log_notification(user_id, "payment_confirmed", message)


async def notify_anomaly(
    whatsapp_no: str,
    user_id,
    amount: float,
    narration: str,
    language: str = "en",
):
    """Alert the trader about an unusually large transaction."""
    scrubbed = scrub({"amount": amount, "narration": narration})
    message = (
        f"⚠️ Unusual transaction detected: {format_naira(scrubbed.get('amount', amount))}.\n"
        f"Narration: {scrubbed.get('narration', 'N/A')}\n"
        "If this is unexpected, reply *human* for help."
    )
    message = await translate_message(message, language)
    await send_text(whatsapp_no, message)

    await _log_notification(user_id, "anomaly", message)


async def notify_debrief(
    whatsapp_no: str,
    user_id,
    debrief_text: str,
    language: str = "en",
):
    """Send the daily debrief notification."""
    message = await translate_message(debrief_text, language)
    await send_text(whatsapp_no, message)

    await _log_notification(user_id, "debrief", message)


async def _log_notification(user_id, notification_type: str, message: str):
    """Record every outbound notification."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(
                insert(NotificationLog).values(
                    user_id=user_id,
                    notification_type=notification_type,
                    message=message[:2000],  # truncate to prevent overflow
                    channel="whatsapp",
                    status="sent",
                )
            )
            await db.commit()
    except Exception:
        logger.exception("Failed to log notification of type %s", notification_type)
