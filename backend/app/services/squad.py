"""
Squad payment service — handles all Squad API interactions.

Supports:
  - Customer registration
  - Virtual account creation
  - Outbound transfers (withdrawals, supplier payments, fee collection)
  - Account balance lookups
  - Webhook signature extraction

All calls use httpx with retry logic for transient failures.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BASE = settings.squad_base_url
HEADERS = {
    "Authorization": f"Bearer {settings.squad_secret_key}",
    "Content-Type": "application/json",
}

MAX_RETRIES = 2
TIMEOUT = 30


async def _request(method: str, path: str, json_data: dict | None = None) -> dict:
    """Make an HTTP request to Squad with retry logic."""
    url = f"{BASE}{path}"
    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.request(method, url, headers=HEADERS, json=json_data)
            if response.status_code >= 500 and attempt < MAX_RETRIES:
                logger.warning(
                    "Squad API %s %s returned %s, retrying (%d/%d)",
                    method, path, response.status_code, attempt + 1, MAX_RETRIES,
                )
                continue
            response.raise_for_status()
            return response.json().get("data", response.json())
        except (httpx.ConnectError, httpx.ReadTimeout) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                logger.warning(
                    "Squad API %s %s connection error, retrying (%d/%d): %s",
                    method, path, attempt + 1, MAX_RETRIES, exc,
                )
                continue
            raise
        except httpx.HTTPStatusError:
            raise

    if last_error:
        raise last_error


async def register_customer(
    first_name: str,
    last_name: str,
    phone: str,
    account_number: str,
    bank_code: str,
) -> dict:
    """Register a new customer with Squad."""
    return await _request("POST", "/api/v1/merchant/customers", {
        "first_name": first_name,
        "last_name": last_name,
        "mobile_num": phone,
        "account_number": account_number,
        "bank_code": bank_code,
    })


async def create_virtual_account(customer_id: str, vault_name: str) -> dict:
    """Create a Squad virtual account for a trader's vault."""
    return await _request("POST", "/api/v1/virtual-account", {
        "customer_identifier": customer_id,
        "preferred_bank": "wema-bank",
        "account_name": vault_name,
    })


async def transfer(
    amount: float,
    bank_code: str,
    account_number: str,
    account_name: str,
    narration: str,
    reference: str,
) -> dict:
    """Execute an outbound transfer (withdrawal, payment, or fee)."""
    return await _request("POST", "/api/v1/payout/transfer", {
        "amount": int(amount * 100),  # Convert naira to kobo
        "bank_code": bank_code,
        "account_number": account_number,
        "account_name": account_name,
        "narration": narration,
        "transaction_reference": reference,
        "currency_id": "NGN",
    })


async def get_virtual_account_balance(account_number: str) -> dict:
    """Fetch the balance of a Squad virtual account."""
    try:
        return await _request("GET", f"/api/v1/virtual-account/balance/{account_number}")
    except Exception:
        logger.exception("Failed to fetch balance for account %s", account_number)
        return {"balance": 0}


async def get_transfer_status(reference: str) -> dict:
    """Check the status of an outbound transfer."""
    try:
        return await _request("GET", f"/api/v1/payout/requery/{reference}")
    except Exception:
        logger.exception("Failed to requery transfer %s", reference)
        return {"status": "unknown"}


def extract_webhook_signature(headers: dict) -> str:
    """Extract the Squad webhook signature from request headers."""
    return (
        headers.get("x-squad-signature")
        or headers.get("squad-signature")
        or headers.get("x-signature")
        or ""
    )
