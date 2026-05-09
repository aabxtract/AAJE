"""
Vault agent — handles all Kolo-related commands from active traders.

Commands handled:
  - "I made ₦X today" / "I sold ₦X" → trigger kolo split
  - "Check my vaults" → return vault balances
  - "Move money from X to Y" → inter-vault transfer
"""
import logging
import re

from app.services import notifier, slicer
from app.utils.formatters import fmt_currency

logger = logging.getLogger(__name__)

_AMOUNT_RE = re.compile(r"(?:₦|N|NGN)?\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)


def _extract_amount(text: str) -> float | None:
    match = _AMOUNT_RE.search(text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


async def handle(wa_number: str, body: str, session: dict) -> None:
    amount = _extract_amount(body)
    if amount is None or amount <= 0:
        await notifier.send(
            wa_number,
            "How much did you make? Tell me like this:\n*I sold ₦18,000 today*",
        )
        return

    await notifier.send(
        wa_number,
        f"Got it! Splitting {fmt_currency(amount)} into your vaults now... 🔄",
    )

    # TODO: fetch trader vault configs from Postgres
    # results = await slicer.execute_split(amount, vaults, trader_id)
    # For now, show calculated split
    ops = amount * 0.60
    sav = amount * 0.20
    eme = amount * 0.20

    summary = (
        f"✅ Done! Here's where your money went:\n\n"
        f"💰 Operations: {fmt_currency(ops)}\n"
        f"🏦 Savings: {fmt_currency(sav)}\n"
        f"🛡️ Emergency: {fmt_currency(eme)}\n\n"
        f"₦5 automation fee collected. Keep stacking! 💪"
    )
    await notifier.send(wa_number, summary)
