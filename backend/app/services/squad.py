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
import hashlib

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


class SquadAccountLimitError(Exception):
    """Raised when Squad sandbox refuses more virtual account creation."""


def _is_account_limit_response(response: httpx.Response) -> bool:
    if response.status_code != 422:
        return False
    try:
        message = (response.json().get("message") or "").lower()
    except ValueError:
        message = response.text.lower()
    return "account opening limit" in message


def _mock_virtual_account(customer_id: str) -> dict:
    digest = hashlib.sha256(customer_id.encode("utf-8")).hexdigest()
    account_number = f"88{int(digest[:8], 16) % 100_000_000:08d}"
    logger.warning(
        "Using mock Squad virtual account %s for customer_identifier=%s",
        account_number,
        customer_id,
    )
    return {
        "customer_identifier": customer_id,
        "account_number": account_number,
        "virtual_account_number": account_number,
        "account_id": f"mock-{digest[:16]}",
        "id": f"mock-{digest[:16]}",
        "mock": True,
    }


async def _request(method: str, path: str, json_data: dict | None = None) -> dict:
    """Make an HTTP request to Squad with retry logic."""
    url = f"{BASE}{path}"
    if json_data:
        logger.info("Squad API request %s %s payload: %s", method, path, json_data)
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
            if response.status_code >= 400:
                logger.error(
                    "Squad API %s %s returned %s: %s",
                    method, path, response.status_code, response.text,
                )
                if path == "/virtual-account" and _is_account_limit_response(response):
                    raise SquadAccountLimitError(response.text)
            else:
                logger.info(
                    "Squad API %s %s returned %s: %s",
                    method, path, response.status_code, response.text,
                )
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
    middle_name: str,
    last_name: str,
    phone: str,
    account_number: str,
    bank_code: str,
) -> dict:
    """
    Register a new customer with Squad.

    Squad sandbox combines registration + virtual account creation into one
    POST /virtual-account call.  We call it here with a dummy vault name
    just to get the customer_identifier back.  The actual per-stream
    accounts are created in create_virtual_account().

    Returns a dict containing at least ``customer_identifier``.
    """
    import uuid
    customer_id = f"AAJE-{uuid.uuid4().hex[:12]}"
    # Squad expects local Nigerian format starting with 0
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("234") and len(digits) > 10:
        clean_phone = "0" + digits[3:]
    else:
        clean_phone = digits[-11:].zfill(11)
        if not clean_phone.startswith("0"):
            clean_phone = "0" + clean_phone[1:]
    payload = {
        "customer_identifier": customer_id,
        "first_name": first_name,
        "last_name": last_name,
        "middle_name": middle_name,
        "mobile_num": clean_phone,
        "email": f"{customer_id}@aaje.app",
        "bvn": "22222222222",               # Squad sandbox accepts test BVN
        "dob": "01/01/1990",
        "gender": "1",
        "address": "Lagos",
        "beneficiary_account": account_number,
    }
    try:
        result = await _request("POST", "/virtual-account", payload)
    except SquadAccountLimitError:
        if not settings.squad_mock_on_account_limit:
            raise
        result = _mock_virtual_account(customer_id)
    # Normalise the response so callers can find the id under any key
    result.setdefault("customer_identifier", customer_id)
    return result


async def create_virtual_account(
    customer_id: str,
    first_name: str,
    middle_name: str,
    last_name: str,
    phone: str,
    beneficiary_account: str,
) -> dict:
    """
    Create a Squad virtual account for a trader's vault.

    Squad B2C model requires full customer info for every account creation.
    We use a unique customer_id per vault to allow multiple accounts.
    """
    # Squad expects local Nigerian format starting with 0
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("234") and len(digits) > 10:
        clean_phone = "0" + digits[3:]
    else:
        clean_phone = digits[-11:].zfill(11)
        if not clean_phone.startswith("0"):
            clean_phone = "0" + clean_phone[1:]
    payload = {
        "customer_identifier": customer_id,
        "first_name": first_name,
        "last_name": last_name,
        "middle_name": middle_name,
        "mobile_num": clean_phone,
        "email": f"{customer_id}@aaje.app",
        "bvn": "22222222222",               # Squad sandbox accepts test BVN
        "dob": "01/01/1990",
        "gender": "1",
        "address": "Lagos",
        "beneficiary_account": beneficiary_account,
    }
    try:
        return await _request("POST", "/virtual-account", payload)
    except SquadAccountLimitError:
        if not settings.squad_mock_on_account_limit:
            raise
        return _mock_virtual_account(customer_id)


async def transfer(
    amount: float,
    bank_code: str,
    account_number: str,
    account_name: str,
    narration: str,
    reference: str,
) -> dict:
    """Execute an outbound transfer (withdrawal, payment, or fee)."""
    return await _request("POST", "/payout/transfer", {
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
        return await _request("GET", f"/virtual-account/balance/{account_number}")
    except Exception:
        logger.exception("Failed to fetch balance for account %s", account_number)
        return {"balance": 0}


async def get_transfer_status(reference: str) -> dict:
    """Check the status of an outbound transfer."""
    try:
        return await _request("GET", f"/payout/requery/{reference}")
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
