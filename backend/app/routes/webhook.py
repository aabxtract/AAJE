"""
Twilio WhatsApp inbound webhook.

Flow:
  1. Validate Twilio signature → 403 on failure
  2. Parse incoming form data
  3. Ack immediately with empty TwiML (< 5 seconds)
  4. Dispatch to session router as a background task
"""
import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Form, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from twilio.request_validator import RequestValidator

from app.config import settings
from app.services.session import route_message

logger = logging.getLogger(__name__)
router = APIRouter()

_validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)


def _validate_twilio(request_url: str, params: dict, signature: str) -> bool:
    return _validator.validate(request_url, params, signature)


@router.post("/twilio", response_class=PlainTextResponse)
async def twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    X_Twilio_Signature: str = Header(default=""),
    From: str = Form(...),
    Body: str = Form(default=""),
    MediaUrl0: str = Form(default=None),
    MediaContentType0: str = Form(default=None),
    NumMedia: str = Form(default="0"),
):
    # Signature validation
    form_data = dict(await request.form())
    if not _validate_twilio(str(request.url), form_data, X_Twilio_Signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    wa_number = From.replace("whatsapp:", "")

    background_tasks.add_task(
        route_message,
        wa_number=wa_number,
        body=Body.strip(),
        media_url=MediaUrl0,
        media_content_type=MediaContentType0,
    )

    # Empty TwiML ack — Twilio requires a 200 response within 5 seconds
    return "<?xml version='1.0' encoding='UTF-8'?><Response></Response>"
