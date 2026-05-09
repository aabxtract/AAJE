"""
Twilio WhatsApp inbound webhook.

Flow:
  1. Validate Twilio signature → 403 on failure
  2. Rate limit check → 10 messages/minute max
  3. Ack immediately with empty MessagingResponse (< 5 seconds)
  4. Dispatch to session router as a BackgroundTask

Uses BackgroundTasks instead of asyncio.create_task because:
  - Errors propagate through FastAPI's logging (no silent failures)
  - Tasks are tracked by the ASGI server for graceful shutdown
  - It's the idiomatic FastAPI pattern for this use case
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from app.config import settings
from app.redis import set_rate_limit

logger = logging.getLogger(__name__)
router = APIRouter()


async def process_message_safe(
    sender: str,
    message: str,
    media_url: str | None,
    media_type: str | None,
):
    """Wrapper that ensures background task errors are always logged."""
    try:
        from app.services.session import route_message
        await route_message(sender, message, media_url, media_type)
    except Exception:
        logger.exception("Background task failed for %s", sender)


@router.post("/twilio", response_class=PlainTextResponse)
async def twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(""),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None),
    NumMedia: int = Form(0),
):
    # Validate Twilio signature
    validator = RequestValidator(settings.twilio_auth_token)
    form_data = await request.form()
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)

    if not validator.validate(url, dict(form_data), signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    sender = From.replace("whatsapp:", "")

    # Rate limiting — max 10 messages per minute
    count = await set_rate_limit(sender)
    if count > 10:
        resp = MessagingResponse()
        resp.message("Please slow down. Try again in a minute.")
        return str(resp)

    # Dispatch to background — Twilio 5-second rule
    background_tasks.add_task(
        process_message_safe,
        sender,
        Body.strip(),
        MediaUrl0,
        MediaContentType0,
    )

    # Empty ack — Twilio requires 200 response within 5 seconds
    resp = MessagingResponse()
    return str(resp)
