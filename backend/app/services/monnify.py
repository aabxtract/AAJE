from __future__ import annotations

import base64
import logging
from typing import Optional

import httpx

from app.config import settings
from app.redis import get_monnify_token, set_monnify_token

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class MonnifyError(RuntimeError):
    """Raised on a non-success Monnify response. The order route should
    catch this, return a friendly error to the customer, and never write
    a payment_link the customer can't actually use."""


def _ensure_keys() -> None:
    if not settings.monnify_api_key or not settings.monnify_secret_key:
        raise MonnifyError("Monnify is not configured (MONNIFY_API_KEY/SECRET_KEY missing)")
    if not settings.monnify_contract_code:
        raise MonnifyError("Monnify is not configured (MONNIFY_CONTRACT_CODE missing)")


def _base() -> str:
    return settings.monnify_base_url.rstrip("/")


def _auth_header() -> dict[str, str]:
    raw = f"{settings.monnify_api_key}:{settings.monnify_secret_key}".encode("utf-8")
    return {"Authorization": "Basic " + base64.b64encode(raw).decode("ascii")}


async def get_access_token(force_refresh: bool = False) -> str:
    """Return a valid bearer token. Cached in Redis for 50 min."""
    _ensure_keys()
    if not force_refresh:
        cached = await get_monnify_token()
        if cached:
            return cached

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(f"{_base()}/api/v1/auth/login", headers=_auth_header())

    if resp.status_code != 200:
        logger.error("Monnify auth failed: %s %s", resp.status_code, resp.text[:300])
        raise MonnifyError(f"Monnify auth returned {resp.status_code}")

    body = resp.json()
    if not body.get("requestSuccessful"):
        logger.error("Monnify auth unsuccessful: %s", body)
        raise MonnifyError(body.get("responseMessage") or "Monnify auth failed")

    token = (body.get("responseBody") or {}).get("accessToken")
    if not token:
        raise MonnifyError("Monnify auth response missing accessToken")

    expires_in = int((body.get("responseBody") or {}).get("expiresIn") or 3600)
    cache_ttl = max(60, expires_in - 600)
    await set_monnify_token(token, cache_ttl)
    return token


async def _bearer_request(
    method: str,
    path: str,
    json: Optional[dict] = None,
) -> dict:
    """Issue a bearer-authenticated Monnify call. Refreshes the token once
    on 401, then gives up. Returns the parsed JSON body."""
    token = await get_access_token()
    url = f"{_base()}{path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.request(method, url, headers=headers, json=json)
        if resp.status_code == 401:
            token = await get_access_token(force_refresh=True)
            headers["Authorization"] = f"Bearer {token}"
            resp = await client.request(method, url, headers=headers, json=json)

    if resp.status_code >= 400:
        logger.error("Monnify %s %s -> %s: %s", method, path, resp.status_code, resp.text[:300])
        raise MonnifyError(f"Monnify {method} {path} returned {resp.status_code}")

    body = resp.json()
    if not body.get("requestSuccessful", True):
        logger.error("Monnify %s %s unsuccessful: %s", method, path, body)
        raise MonnifyError(body.get("responseMessage") or "Monnify request failed")
    return body


async def create_payment_link(
    amount: float,
    order_ref: str,
    customer_name: str,
    customer_email: Optional[str] = None,
    description: Optional[str] = None,
    redirect_url: Optional[str] = None,
) -> dict:
    """Create a Monnify payment link.

    Returns ``{"checkout_url": str, "transaction_reference": str, "payment_reference": str}``.
    Raises ``MonnifyError`` on failure — the caller must NOT save an order
    with a fake or empty payment_link.
    """
    _ensure_keys()

    payload = {
        "amount": float(amount),
        "customerName": customer_name[:100],
        "customerEmail": customer_email or "noreply@aaje.store",
        "paymentReference": order_ref,
        "paymentDescription": (description or f"Order {order_ref}")[:100],
        "currencyCode": "NGN",
        "contractCode": settings.monnify_contract_code,
        "redirectUrl": redirect_url or settings.monnify_redirect_url or "",
        "paymentMethods": ["CARD", "ACCOUNT_TRANSFER"],
    }

    body = await _bearer_request(
        "POST", "/api/v1/merchant/transactions/init-transaction", json=payload
    )
    response_body = body.get("responseBody") or {}
    checkout_url = response_body.get("checkoutUrl")
    if not checkout_url:
        raise MonnifyError("Monnify response missing checkoutUrl")

    return {
        "checkout_url": checkout_url,
        "transaction_reference": response_body.get("transactionReference") or "",
        "payment_reference": response_body.get("paymentReference") or order_ref,
    }


async def verify_payment(payment_reference: str) -> dict:
    """Look up a transaction by paymentReference.

    Returns ``{"paid": bool, "status": str, "amount_paid": float,
    "transaction_reference": str}``.
    """
    body = await _bearer_request(
        "GET", f"/api/v2/transactions/{payment_reference}"
    )
    response_body = body.get("responseBody") or {}
    return {
        "paid": bool(response_body.get("paid")),
        "status": response_body.get("paymentStatus") or "UNKNOWN",
        "amount_paid": float(response_body.get("amountPaid") or 0),
        "transaction_reference": response_body.get("transactionReference") or "",
    }
