import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Request, Response
from typing import Annotated

from app.config import settings
from app.redis import set_rate_limit
from app.services.session import route_message

logger = logging.getLogger(__name__)
router = APIRouter(tags=["whatsapp"])

_RATE_LIMIT_MAX = 5  # messages per 60-second window per sender


@router.get("/webhook/whatsapp")
async def verify_webhook(
    hub_mode: Annotated[str, Query(alias="hub.mode")] = "",
    hub_challenge: Annotated[str, Query(alias="hub.challenge")] = "",
    hub_verify_token: Annotated[str, Query(alias="hub.verify_token")] = "",
):
    if not settings.meta_webhook_verify_token:
        logger.error("Webhook verify token not configured — refusing verification")
        raise HTTPException(status_code=503, detail="Webhook not configured")
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/webhook/whatsapp")
async def receive_webhook(
    request: Request,
    background: BackgroundTasks,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
):
    raw_body = await request.body()

    # Validate HMAC signature. Outside development, refuse to process without
    # a configured secret. In development, validate only if a secret is set.
    if settings.app_env != "development":
        if not settings.meta_app_secret:
            logger.error("META_APP_SECRET missing in non-dev environment")
            raise HTTPException(status_code=503, detail="Webhook not configured")
        if not x_hub_signature_256 or not _valid_signature(raw_body, x_hub_signature_256):
            logger.warning("WhatsApp webhook: invalid signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
    elif settings.meta_app_secret:
        if not x_hub_signature_256 or not _valid_signature(raw_body, x_hub_signature_256):
            logger.warning("WhatsApp webhook: invalid signature (dev)")
            raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(raw_body) if raw_body else {}
    except Exception:
        payload = {}

    # Return 200 to Meta before any processing
    background.add_task(_process_webhook, payload)
    return Response(status_code=200)


async def _process_webhook(payload: dict) -> None:
    from app.database import AsyncSessionLocal

    try:
        for entry in payload.get("entry") or []:
            for change in entry.get("changes") or []:
                value = change.get("value") or {}
                for msg in value.get("messages") or []:
                    sender = msg.get("from")
                    if not sender:
                        continue

                    count = await set_rate_limit(sender)
                    if count > _RATE_LIMIT_MAX:
                        logger.warning("Rate limit: %s (%d msg/min)", sender, count)
                        continue

                    text = _extract_text(msg)
                    if text is None:
                        continue

                    async with AsyncSessionLocal() as db:
                        await route_message(sender, text, db)
    except Exception:
        logger.exception("Error processing WhatsApp webhook payload")


def _extract_text(msg: dict) -> str | None:
    msg_type = msg.get("type")
    if msg_type == "text":
        return (msg.get("text") or {}).get("body", "").strip() or None
    if msg_type == "interactive":
        interactive = msg.get("interactive") or {}
        if interactive.get("type") == "list_reply":
            return (interactive.get("list_reply") or {}).get("title", "").strip() or None
        if interactive.get("type") == "button_reply":
            return (interactive.get("button_reply") or {}).get("title", "").strip() or None
    return None


def _valid_signature(raw_body: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(
        settings.meta_app_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
