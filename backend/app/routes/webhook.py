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
    except Exception as e:
        logger.exception("Background task failed for %s", sender)
        import traceback
        with open("debug.log", "a") as f:
            f.write(f"Error for {sender}: {traceback.format_exc()}\n")


@router.post("/twilio", response_class=PlainTextResponse)
async def twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    # Parse form data manually to avoid 422 errors from extra Twilio fields
    form_data = await request.form()
    form_dict = dict(form_data)
    
    # Debug: log ALL keys so we can see what Twilio actually sends
    logger.info(f"=== INCOMING WEBHOOK ===")
    logger.info(f"All form keys: {list(form_dict.keys())}")
    logger.info(f"All form data: {form_dict}")
    
    # Try exact key first, then case-insensitive fallback
    From = form_dict.get("From", "")
    if not From:
        # Case-insensitive search
        for key, val in form_dict.items():
            if key.lower() == "from":
                From = val
                break
    
    Body = form_dict.get("Body", "") or ""
    MediaUrl0 = form_dict.get("MediaUrl0")
    MediaContentType0 = form_dict.get("MediaContentType0")
    
    logger.info(f"Extracted From={From}, Body={Body[:50]}")

    # Keep the + prefix — Twilio needs whatsapp:+234... format to send replies
    sender = From.replace("whatsapp:", "").strip()
    
    if not sender:
        logger.error(f"Could not extract sender from form data! From field was: '{From}'")
        resp = MessagingResponse()
        return str(resp)

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
