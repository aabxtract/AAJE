import logging

from sqlalchemy import insert

from app.database import AsyncSessionLocal
from app.models.notification_log import NotificationLog
from app.services.whatsapp_client import send_text
from app.utils.formatters import format_naira

logger = logging.getLogger(__name__)


async def notify_order_received(
    whatsapp_no: str,
    user_id,
    order_reference: str,
    amount: float,
    customer_name: str | None = None,
):
    customer_line = f"\nCustomer: {customer_name}" if customer_name else ""
    message = (
        f"New storefront order received.\n"
        f"Order: {order_reference}\n"
        f"Amount: {format_naira(amount)}{customer_line}\n\n"
        "Open your dashboard or reply 'recent orders'."
    )
    await _send_and_log(whatsapp_no, user_id, "order_received", message)


async def notify_payment_received(
    whatsapp_no: str,
    user_id,
    amount: float,
    reference: str,
):
    message = (
        f"Payment confirmed for your storefront.\n"
        f"Amount: {format_naira(amount)}\n"
        f"Ref: {reference}\n\n"
        "Inventory and sales have been updated."
    )
    await _send_and_log(whatsapp_no, user_id, "payment_received", message)


async def notify_low_stock(
    whatsapp_no: str,
    user_id,
    products: list[dict],
):
    if not products:
        return
    lines = ["Low stock alert."]
    for product in products[:5]:
        lines.append(f"- {product.get('name', 'Product')}: {product.get('stock', 0)} left")
    lines.append("\nReply 'low stock' or update stock from your dashboard.")
    await _send_and_log(whatsapp_no, user_id, "low_stock", "\n".join(lines))


async def notify_daily_sales_summary(
    whatsapp_no: str,
    user_id,
    revenue: float,
    order_count: int,
    top_product: str | None = None,
):
    top_line = f"\nTop product: {top_product}" if top_product else ""
    message = (
        f"Daily sales summary.\n"
        f"Orders: {order_count}\n"
        f"Revenue: {format_naira(revenue)}{top_line}\n\n"
        "Reply 'what sold today' for details."
    )
    await _send_and_log(whatsapp_no, user_id, "daily_sales_summary", message)


async def notify_withdrawal(
    whatsapp_no: str,
    user_id,
    amount: float,
    stream_name: str,
    reference: str,
    language: str = "en",
):
    message = (
        f"Withdrawal confirmed.\n"
        f"Amount: {format_naira(amount)}\n"
        f"Destination: {stream_name}\n"
        f"Ref: {reference}"
    )
    await _send_and_log(whatsapp_no, user_id, "withdrawal_confirmed", message)


async def notify_payment(
    whatsapp_no: str,
    user_id,
    amount: float,
    supplier_name: str,
    reference: str,
    language: str = "en",
):
    message = (
        f"Payment confirmed.\n"
        f"Amount: {format_naira(amount)}\n"
        f"Recipient: {supplier_name}\n"
        f"Ref: {reference}"
    )
    await _send_and_log(whatsapp_no, user_id, "payment_confirmed", message)


async def notify_split(
    whatsapp_no: str,
    user_id,
    amount: float,
    split_lines: list[dict],
    language: str = "en",
):
    lines = [
        "Storefront payment received.",
        f"Amount: {format_naira(amount)}",
    ]
    for entry in split_lines:
        stream_name = entry.get("stream_name", "Store balance")
        lines.append(f"- {stream_name}: {format_naira(entry.get('amount', 0))}")
    await _send_and_log(whatsapp_no, user_id, "payment_received", "\n".join(lines))


async def notify_anomaly(
    whatsapp_no: str,
    user_id,
    amount: float,
    narration: str,
    language: str = "en",
):
    message = (
        "Storefront payment needs review.\n"
        f"Amount: {format_naira(amount)}\n"
        f"Note: {narration or 'No narration'}\n\n"
        "Open your dashboard to review this activity."
    )
    await _send_and_log(whatsapp_no, user_id, "payment_review", message)


async def notify_debrief(
    whatsapp_no: str,
    user_id,
    debrief_text: str,
    language: str = "en",
):
    await _send_and_log(whatsapp_no, user_id, "daily_sales_summary", debrief_text)


async def _send_and_log(whatsapp_no: str, user_id, notification_type: str, message: str):
    await send_text(whatsapp_no, message)
    await _log_notification(user_id, notification_type, message)


async def _log_notification(user_id, notification_type: str, message: str):
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(
                insert(NotificationLog).values(
                    user_id=user_id,
                    notification_type=notification_type,
                    message=message[:2000],
                    channel="whatsapp",
                    status="sent",
                )
            )
            await db.commit()
    except Exception:
        logger.exception("Failed to log notification of type %s", notification_type)
