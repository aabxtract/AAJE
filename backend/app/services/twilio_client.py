"""
Twilio outbound messaging client.

Handles:
  - Outbound text messages
  - Outbound voice notes (via public URL)
  - Interactive buttons (numbered list for sandbox)
  - CTA buttons (link with label)
  - Media messages (images, documents)
"""
from twilio.rest import Client
from app.config import settings

client = Client(
    settings.twilio_account_sid,
    settings.twilio_auth_token,
)

FROM = settings.twilio_whatsapp_from


async def send_text(to: str, message: str):
    """Send a plain text WhatsApp message."""
    client.messages.create(
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
    client.messages.create(
        from_=FROM,
        to=f"whatsapp:{to}",
        media_url=[audio_url],
    )


async def send_media(to: str, media_url: str, caption: str = ""):
    """Send an image or document with optional caption."""
    client.messages.create(
        from_=FROM,
        to=f"whatsapp:{to}",
        media_url=[media_url],
        body=caption,
    )
