import hashlib
import hmac
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.redis import set_rate_limit

logger = logging.getLogger(__name__)
router = APIRouter()


def _mask_sender(sender: str | None) -> str:
    if not sender:
        return "unknown"
    return f"{sender[:4]}...{sender[-4:]}" if len(sender) > 8 else "masked"


def _verify_meta_signature(payload: bytes, signature: str) -> bool:
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.meta_app_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


async def process_message_safe(sender: str, message: str):
    try:
        from app.services.session import route_message

        await route_message(sender, message)
    except Exception:
        logger.exception("Message processing failed for %s", sender)
        try:
            from app.services.whatsapp_client import send_text

            await send_text(sender, "Something went wrong. Please try again in a moment.")
        except Exception:
            logger.exception("Failed to send fallback error message to %s", sender)


@router.get("/webhook/whatsapp", response_class=PlainTextResponse)
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        logger.info("Meta WhatsApp webhook verification succeeded")
        return hub_challenge
    logger.warning("Meta WhatsApp webhook verification failed: mode=%s", hub_mode)
    raise HTTPException(status_code=403, detail="Invalid verify token")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")
    if not _verify_meta_signature(payload, signature):
        logger.warning(
            "Rejected WhatsApp webhook: invalid signature header present=%s payload_bytes=%s",
            bool(signature),
            len(payload),
        )
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()
    value = (
        data.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
    )
    messages = value.get("messages") or []
    if not messages:
        logger.info("Ignored WhatsApp webhook without messages. keys=%s", sorted(value.keys()))
        return {"status": "ignored"}

    message = messages[0]
    sender = message.get("from")
    message_type = message.get("type")
    if not sender or message_type != "text":
        logger.info(
            "Ignored WhatsApp message: sender=%s type=%s",
            _mask_sender(sender),
            message_type,
        )
        return {"status": "ignored"}

    body = (message.get("text") or {}).get("body", "").strip()
    if not body:
        logger.info("Ignored empty WhatsApp text from %s", _mask_sender(sender))
        return {"status": "ignored"}

    count = await set_rate_limit(sender)
    if count > 10:
        from app.services.whatsapp_client import send_text

        logger.warning("Rate limited WhatsApp sender %s", _mask_sender(sender))
        await send_text(sender, "Please slow down. Try again in a minute.")
        return {"status": "rate_limited"}

    logger.info("Received WhatsApp text from %s; queued processing", _mask_sender(sender))
    background_tasks.add_task(process_message_safe, sender, body)
    return {"status": "received"}
