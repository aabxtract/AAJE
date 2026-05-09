"""
Twilio outbound messaging client.

Handles:
  - Outbound text messages
  - Outbound media messages (voice notes via public URL)
  - Interactive button messages

This is used by background tasks AFTER the webhook has already acked.
"""
import logging

from twilio.rest import Client

from app.config import settings

logger = logging.getLogger(__name__)

_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
_FROM = settings.TWILIO_WHATSAPP_FROM


def _to_wa(number: str) -> str:
    """Ensure number is in whatsapp:+234... format."""
    if not number.startswith("whatsapp:"):
        return f"whatsapp:{number}"
    return number


async def send_text(to: str, body: str) -> str:
    """Send a plain text WhatsApp message. Returns Twilio message SID."""
    msg = _client.messages.create(
        from_=_FROM,
        to=_to_wa(to),
        body=body,
    )
    logger.info("Text sent | to=%s | sid=%s", to, msg.sid)
    return msg.sid


async def send_audio(to: str, audio_url: str, caption: str = "") -> str:
    """Send a voice note (audio file at public URL) as WhatsApp media."""
    msg = _client.messages.create(
        from_=_FROM,
        to=_to_wa(to),
        body=caption,
        media_url=[audio_url],
    )
    logger.info("Audio sent | to=%s | sid=%s", to, msg.sid)
    return msg.sid


async def send_buttons(to: str, body: str, buttons: list[dict]) -> str:
    """
    Send interactive button message.
    buttons: [{"id": "yes", "title": "Yes"}, ...]
    Note: Twilio WhatsApp interactive messages require approved templates in production.
    """
    # For sandbox/hackathon: fall back to numbered text menu
    menu = body + "\n\n"
    for i, btn in enumerate(buttons, 1):
        menu += f"{i}. {btn['title']}\n"
    menu += "\nReply with the number of your choice."
    return await send_text(to, menu)
