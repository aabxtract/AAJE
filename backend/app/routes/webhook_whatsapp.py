"""
Twilio WhatsApp webhook (MVP).

Twilio sends ``application/x-www-form-urlencoded`` POSTs. There is no GET
verification step (Twilio uses signed POSTs only). We validate
``X-Twilio-Signature`` and return an empty ``<Response/>`` TwiML body.

Heavy work runs in BackgroundTasks AFTER the 200 is returned (CLAUDE.md §11).
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, Response

from app.config import settings
from app.redis import set_rate_limit
from app.services.session import route_message

logger = logging.getLogger(__name__)
router = APIRouter(tags=["whatsapp"])

_RATE_LIMIT_MAX = 10  # messages per 60-second window per sender
_TWIML_EMPTY = '<?xml version="1.0" encoding="UTF-8"?><Response/>'


@router.post("/webhook/whatsapp")
async def receive_webhook(
    request: Request,
    background: BackgroundTasks,
    x_twilio_signature: Annotated[str | None, Header()] = None,
):
    raw_body = await request.body()
    form = await request.form()
    params = {k: str(v) for k, v in form.items()}

    if not _signature_ok(request, params, x_twilio_signature):
        logger.warning("Twilio webhook: invalid signature from %s", params.get("From"))
        raise HTTPException(status_code=403, detail="Invalid signature")

    sender = _strip_whatsapp_prefix(params.get("From"))
    body = (params.get("Body") or "").strip()

    if sender and body:
        background.add_task(_process_message, sender, body)

    return Response(content=_TWIML_EMPTY, media_type="application/xml")


async def _process_message(sender: str, body: str) -> None:
    from app.database import AsyncSessionLocal

    try:
        count = await set_rate_limit(sender)
        if count > _RATE_LIMIT_MAX:
            logger.warning("Rate limit: %s (%d msg/min)", sender, count)
            return

        async with AsyncSessionLocal() as db:
            await route_message(sender, body, db)
    except Exception:
        logger.exception("Error processing Twilio webhook message from %s", sender)


def _strip_whatsapp_prefix(value: str | None) -> str:
    raw = str(value or "").strip()
    if raw.lower().startswith("whatsapp:"):
        raw = raw.split(":", 1)[1]
    digits = "".join(ch for ch in raw if ch.isdigit())
    return digits


def _signature_ok(request: Request, params: dict, signature: str | None) -> bool:
    if not settings.twilio_webhook_validate:
        return True
    if not signature or not settings.twilio_auth_token:
        return False

    try:
        from twilio.request_validator import RequestValidator
    except ImportError:
        logger.error("twilio package not installed; cannot validate webhook signature")
        return False

    validator = RequestValidator(settings.twilio_auth_token)
    url = _signed_url(request)
    return validator.validate(url, params, signature)


def _signed_url(request: Request) -> str:
    """Reconstruct the URL Twilio signed. If APP_PUBLIC_URL is set
    (typical behind a reverse proxy / ngrok), prefer it."""
    if settings.app_public_url:
        base = settings.app_public_url.rstrip("/")
        return f"{base}{request.url.path}"
    return str(request.url)
