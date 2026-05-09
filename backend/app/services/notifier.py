"""
Notifier — outbound message orchestrator.

Combines twilio_client + yarngpt to deliver either:
  - Text-only message
  - Text + voice note (translated via YarnGPT)

Decides based on trader language preference stored in session/DB.
"""
import logging

from app.services import twilio_client, yarngpt

logger = logging.getLogger(__name__)


async def send(
    wa_number: str,
    text: str,
    language: str = "english",
    voice: bool = False,
) -> None:
    """
    Send a message to a trader.
    If voice=True and language is not English, also send a YarnGPT voice note.
    """
    await twilio_client.send_text(wa_number, text)

    if voice and language in yarngpt.SUPPORTED_LANGUAGES:
        audio_url = await yarngpt.synthesize_and_upload(text, language)
        if audio_url:
            await twilio_client.send_audio(wa_number, audio_url)
        else:
            logger.warning("Voice note generation failed for %s, text-only sent", wa_number)
