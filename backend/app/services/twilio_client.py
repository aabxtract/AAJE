"""
Twilio outbound messaging client.

Handles:
  - Outbound text messages
  - Outbound voice notes (via public URL)
  - Interactive buttons (numbered list for sandbox)
  - CTA buttons (link with label)
  - Media messages (images, documents)
"""
import logging
import time
from twilio.rest import Client
from app.config import settings

logger = logging.getLogger(__name__)

client = Client(
    settings.twilio_account_sid,
    settings.twilio_auth_token,
)

FROM = settings.twilio_whatsapp_from


def _send_with_retry(max_retries=3, **kwargs):
    """Send a Twilio message with retry logic for transient connection errors."""
    for attempt in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except Exception as e:
            logger.warning(f"Twilio send attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait 1 second before retrying
            else:
                logger.error(f"Twilio send failed after {max_retries} attempts")
                raise


async def send_text(to: str, message: str):
    """Send a plain text WhatsApp message."""
    _send_with_retry(
        from_=FROM,
        to=f"whatsapp:{to}",
        body=message,
    )


async def send_buttons(to: str, body: str, buttons: list[str]):
    """
    Send interactive buttons.
    Sandbox fallback: buttons rendered as a numbered list
    since Twilio sandbox doesn't support interactive buttons.
    """
    numbered = "\n".join(
        [f"{i+1}. {b}" for i, b in enumerate(buttons)]
    )
    await send_text(to, f"{body}\n\n{numbered}\n\nReply with the number.")


async def send_cta_button(
    to: str, body: str, button_label: str, url: str
):
    """Send a CTA button with a link (for Mono Connect etc)."""
    await send_text(to, f"{body}\n\n👉 {button_label}:\n{url}")


async def send_voice_note(to: str, audio_url: str):
    """Send a voice note (audio file at public URL)."""
    _send_with_retry(
        from_=FROM,
        to=f"whatsapp:{to}",
        media_url=[audio_url],
    )


async def send_media(to: str, media_url: str, caption: str = ""):
    """Send an image or document with optional caption."""
    _send_with_retry(
        from_=FROM,
        to=f"whatsapp:{to}",
        media_url=[media_url],
        body=caption,
    )
