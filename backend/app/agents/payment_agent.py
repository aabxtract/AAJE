"""Payment agent — handles supplier payments and invoice requests."""
import logging

from app.services import notifier

logger = logging.getLogger(__name__)


async def handle(wa_number: str, body: str, session: dict) -> None:
    # TODO: supplier lookup, payment execution, invoice generation
    await notifier.send(
        wa_number,
        "🧾 Who are you paying and how much?\nExample: *Pay Mama Ngozi ₦5,000*",
    )
