"""
Squad financial rails service.

Covers:
  - Virtual account creation (vaults)
  - Transfer execution (splits, withdrawals, ₦5 fee)
  - Account lookup (identity verification fallback)
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_BASE = settings.SQUAD_BASE_URL
_HEADERS = {
    "Authorization": f"Bearer {settings.SQUAD_SECRET_KEY}",
    "Content-Type": "application/json",
}


async def create_virtual_account(
    customer_identifier: str,
    first_name: str,
    last_name: str,
    mobile_num: str,
    email: str,
    bvn: str = "",
) -> dict:
    """Create a Squad virtual account (used per vault per trader)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_BASE}/virtual-account",
            headers=_HEADERS,
            json={
                "customer_identifier": customer_identifier,
                "first_name": first_name,
                "last_name": last_name,
                "mobile_num": mobile_num,
                "email": email,
                "bvn": bvn,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def transfer(
    amount: int,  # in kobo
    bank_code: str,
    account_number: str,
    account_name: str,
    narration: str,
    reference: str,
) -> dict:
    """Execute a Squad transfer (vault split or withdrawal)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_BASE}/payout/transfer",
            headers=_HEADERS,
            json={
                "amount": amount,
                "bank_code": bank_code,
                "account_number": account_number,
                "account_name": account_name,
                "narration": narration,
                "currency": "NGN",
                "reference": reference,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def collect_fee(amount_kobo: int, reference: str) -> dict:
    """Collect the ₦5 behavioral tax to the AAJE revenue account."""
    return await transfer(
        amount=amount_kobo,
        bank_code="000",  # placeholder — Squad internal transfer
        account_number=settings.SQUAD_REVENUE_ACCOUNT,
        account_name="AAJE Revenue",
        narration="AAJE automation fee",
        reference=reference,
    )
