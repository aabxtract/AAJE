"""
Mono service.

Responsibilities:
  - Account name lookup (identity verification during onboarding)
  - Transaction history pull (initial 90-day seed + incremental sync)
  - Connect URL generation (for bank linking deep link)
"""
import logging
import unicodedata

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_BASE = settings.MONO_BASE_URL
_HEADERS = {
    "mono-sec-key": settings.MONO_SECRET_KEY,
    "Content-Type": "application/json",
}


def _normalize_name(name: str) -> str:
    """Uppercase, strip diacritics and extra whitespace for comparison."""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return " ".join(name.upper().split())


async def lookup_account_name(account_number: str, bank_code: str) -> str | None:
    """
    Call Mono account lookup.
    Returns the normalized account name or None on failure.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{_BASE}/v1/accounts/resolve",
                headers=_HEADERS,
                json={"account_number": account_number, "bank_code": bank_code},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            raw_name = data.get("data", {}).get("name", "")
            return _normalize_name(raw_name) if raw_name else None
        except httpx.HTTPError as exc:
            logger.error("Mono account lookup failed: %s", exc)
            return None


def names_match(trader_name: str, mono_name: str) -> bool:
    """Compare trader-provided name against Mono-returned name (normalized)."""
    return _normalize_name(trader_name) == _normalize_name(mono_name)


async def get_transactions(account_id: str, start: str, end: str) -> list[dict]:
    """
    Pull transactions for a linked account.
    start/end: ISO date strings 'YYYY-MM-DD'
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_BASE}/v2/accounts/{account_id}/transactions",
            headers=_HEADERS,
            params={"start": start, "end": end, "paginate": "false"},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
