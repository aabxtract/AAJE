"""Support agent — handles locked accounts and escalations."""
import logging

from app.services import notifier

logger = logging.getLogger(__name__)


async def handle(wa_number: str, body: str, session: dict) -> None:
    await notifier.send(
        wa_number,
        "🔒 Your account is currently under review.\n"
        "Our support team will contact you within 24 hours.\n"
        "If urgent, call 0800-AAJE-NG.",
    )
