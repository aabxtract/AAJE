"""
Twilio WhatsApp client (MVP).

Single surface used by routes/, services/, agents/. Provider swap-friendly:
the June 2026 Meta migration replaces only this file. Callers see
``send_text``, ``send_cta_link``, ``send_image`` regardless of provider.

CLAUDE.md §11 + AGENT_CONTEXT.md §2.
"""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TWILIO_API = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


def _credentials_configured() -> bool:
    return bool(
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_whatsapp_from
    )


def _normalize_to(to: str) -> str:
    """Ensure recipient is ``whatsapp:+E164``. Accepts bare digits, +E164,
    or already-prefixed ``whatsapp:`` strings."""
    raw = str(to or "").strip()
    if not raw:
        raise ValueError("Recipient WhatsApp number is empty")
    if raw.lower().startswith("whatsapp:"):
        body = raw.split(":", 1)[1].strip()
    else:
        body = raw
    digits = "".join(ch for ch in body if ch.isdigit())
    if not digits:
        raise ValueError(f"No digits in WhatsApp number: {to!r}")
    if digits.startswith("0") and len(digits) == 11:
        digits = "234" + digits[1:]
    return f"whatsapp:+{digits}"


async def _post(payload: dict) -> dict:
    if not _credentials_configured():
        recipient = payload.get("To", "unknown")
        if settings.app_env.lower() == "production":
            raise RuntimeError("Twilio credentials are not configured")
        logger.warning(
            "Skipping outbound WhatsApp to %s — Twilio credentials not set.",
            recipient,
        )
        return {"status": "skipped_unconfigured_whatsapp"}

    url = _TWILIO_API.format(sid=settings.twilio_account_sid)
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, data=payload, auth=auth)
    if resp.status_code >= 300:
        logger.error(
            "Twilio WhatsApp error %s sending to %s: %s",
            resp.status_code,
            payload.get("To"),
            resp.text[:500],
        )
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "raw": resp.text[:500]}


async def send_text(to: str, message: str) -> dict:
    """Send a plain WhatsApp text message via Twilio."""
    if not message or not message.strip():
        logger.warning("Attempted to send empty WhatsApp text to %s; skipped.", to)
        return {"status": "skipped_empty"}
    try:
        recipient = _normalize_to(to)
    except ValueError as exc:
        logger.warning("Cannot send WhatsApp: %s", exc)
        return {"status": "invalid_recipient", "detail": str(exc)}

    return await _post({
        "From": settings.twilio_whatsapp_from,
        "To": recipient,
        "Body": message,
    })


async def send_cta_link(to: str, body: str, label: str, url: str) -> dict:
    """Send a body with an inline link. Twilio plain-text version.

    MVP emits the URL inline (WhatsApp auto-linkifies). Phase 2 can upgrade
    to a Content API template with a real URL button using the same signature.
    """
    label = (label or "Open").strip()
    composed = f"{body.rstrip()}\n\n👉 {label}: {url}"
    return await send_text(to, composed)


async def send_image(to: str, image_url: str, caption: str = "") -> dict:
    """Send a WhatsApp media message via Twilio."""
    try:
        recipient = _normalize_to(to)
    except ValueError as exc:
        logger.warning("Cannot send WhatsApp image: %s", exc)
        return {"status": "invalid_recipient", "detail": str(exc)}

    payload: dict[str, Any] = {
        "From": settings.twilio_whatsapp_from,
        "To": recipient,
        "MediaUrl": image_url,
    }
    if caption:
        payload["Body"] = caption
    return await _post(payload)


def build_wa_me_link(buyer_phone: str, prefilled_message: str) -> str:
    """Build a ``https://wa.me/{phone}?text=...`` deep link.

    Used inside the trader's notification so they can message the buyer
    directly from their personal WhatsApp. The AAJE bot never messages the
    buyer — see CLAUDE.md §11.
    """
    digits = "".join(ch for ch in str(buyer_phone or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("0") and len(digits) == 11:
        digits = "234" + digits[1:]
    return f"https://wa.me/{digits}?text={quote(prefilled_message)}"
