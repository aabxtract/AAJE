"""
Mono open banking service — account verification and transaction history.

Supports:
  - Account name lookup (BVN-verified identity confirmation)
  - Transaction history retrieval for analytics
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BANK_CODES = {
    "gtbank": "058", "gtb": "058", "guaranty trust": "058", "guaranty trust bank": "058", "gt bank": "058",
    "access": "044", "access bank": "044",
    "zenith": "057", "zenith bank": "057",
    "first bank": "011", "firstbank": "011", "fbn": "011",
    "uba": "033", "united bank for africa": "033",
    "union": "032", "union bank": "032",
    "fidelity": "070", "fidelity bank": "070",
    "sterling": "232", "sterling bank": "232",
    "stanbic": "221", "stanbic ibtc": "221",
    "polaris": "076", "polaris bank": "076",
    "keystone": "082", "keystone bank": "082",
    "wema": "035", "wema bank": "035",
    "kuda": "50211", "kuda bank": "50211",
    "opay": "999992", "opera": "999992",
    "palmpay": "999991", "palm pay": "999991",
    "moniepoint": "50515", "monie point": "50515",
    "fcmb": "214",
    "ecobank": "050", "eco bank": "050",
    "heritage": "030", "heritage bank": "030",
    "jaiz": "301", "jaiz bank": "301",
    "providus": "101", "providus bank": "101",
    "titan": "102", "titan trust": "102",
}

TIMEOUT = 30


def _headers() -> dict:
    return {
        "mono-sec-key": settings.mono_secret_key,
        "Content-Type": "application/json",
    }


async def lookup_account(account_number: str, bank_code: str) -> dict:
    """Resolve a bank account to get the verified account name."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{settings.mono_base_url}/v1/accounts/resolve",
            headers=_headers(),
            json={"account_number": account_number, "bank_code": bank_code},
        )
    response.raise_for_status()
    return response.json().get("data", response.json())


async def get_account_transactions(
    account_id: str,
    start: str | None = None,
    end: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Fetch transaction history from a linked Mono account.

    Args:
        account_id: The Mono account ID (set after Mono Connect flow).
        start: Start date in DD-MM-YYYY format.
        end: End date in DD-MM-YYYY format.
        limit: Max number of transactions to return.

    Returns:
        List of transaction dicts.
    """
    params = {"paginate": "false", "limit": str(limit)}
    if start:
        params["start"] = start
    if end:
        params["end"] = end

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                f"{settings.mono_base_url}/v1/accounts/{account_id}/transactions",
                headers=_headers(),
                params=params,
            )
        response.raise_for_status()
        data = response.json()
        return data.get("data", data.get("transactions", []))
    except Exception:
        logger.exception("Failed to fetch Mono transactions for %s", account_id)
        return []


async def get_account_info(account_id: str) -> dict:
    """Fetch account details from Mono (balance, type, institution)."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                f"{settings.mono_base_url}/v1/accounts/{account_id}",
                headers=_headers(),
            )
        response.raise_for_status()
        return response.json().get("data", response.json())
    except Exception:
        logger.exception("Failed to fetch Mono account info for %s", account_id)
        return {}
