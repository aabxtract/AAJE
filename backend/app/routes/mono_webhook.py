"""
Mono event webhook.

Events handled:
  - mono.events.account_connected  → account linked, trigger initial 90-day pull
  - mono.events.account_updated    → new transactions, trigger incremental sync
"""
import hashlib
import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_mono_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.MONO_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhook")
async def mono_webhook(
    request: Request,
    mono_webhook_secret: str = Header(default="", alias="mono-webhook-secret"),
):
    payload = await request.body()

    if not _verify_mono_signature(payload, mono_webhook_secret):
        raise HTTPException(status_code=403, detail="Invalid Mono signature")

    event = await request.json()
    event_type = event.get("event")

    logger.info("Mono event received: %s", event_type)

    if event_type == "mono.events.account_connected":
        # TODO: trigger initial 90-day transaction pull
        pass
    elif event_type == "mono.events.account_updated":
        # TODO: trigger incremental transaction sync
        pass

    return {"status": "received"}
