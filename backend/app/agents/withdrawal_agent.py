"""Withdrawal agent — handles trader withdrawal requests from vaults."""
import logging

from app.services import notifier

logger = logging.getLogger(__name__)


async def handle(wa_number: str, body: str, session: dict) -> None:
    # TODO: parse amount + vault, verify PIN, execute Squad transfer
    await notifier.send(
        wa_number,
        "💸 Withdrawal request received. Please enter your PIN to confirm:",
    )
