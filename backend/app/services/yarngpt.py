"""
YarnGPT V3 service.

Pipeline:
  1. Send English text + target language to YarnGPT API
  2. Receive audio bytes (WAV/MP3)
  3. Upload to Supabase Storage public bucket
  4. Return public URL for Twilio to send as WhatsApp audio message
"""
import logging
import uuid

import httpx
from supabase import create_client

from app.config import settings

logger = logging.getLogger(__name__)

_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
_BUCKET = "voice-notes"

SUPPORTED_LANGUAGES = ("yoruba", "igbo", "hausa", "pidgin")


async def synthesize_and_upload(text: str, language: str = "yoruba") -> str | None:
    """
    Translate text to target language and generate TTS audio.
    Returns the public Supabase Storage URL or None on failure.
    """
    if language not in SUPPORTED_LANGUAGES:
        language = "yoruba"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                settings.YARNGPT_API_URL,
                headers={"Authorization": f"Bearer {settings.YARNGPT_API_KEY}"},
                json={"text": text, "language": language},
            )
            resp.raise_for_status()
            audio_bytes = resp.content
        except httpx.HTTPError as exc:
            logger.error("YarnGPT synthesis failed: %s", exc)
            return None

    filename = f"{uuid.uuid4()}.mp3"
    try:
        _supabase.storage.from_(_BUCKET).upload(
            path=filename,
            file=audio_bytes,
            file_options={"content-type": "audio/mpeg"},
        )
        public_url = _supabase.storage.from_(_BUCKET).get_public_url(filename)
        return public_url
    except Exception as exc:
        logger.error("Supabase audio upload failed: %s", exc)
        return None
