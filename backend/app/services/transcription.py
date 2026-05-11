import logging
import httpx
from groq import AsyncGroq
from app.config import settings

logger = logging.getLogger(__name__)
_client = AsyncGroq(api_key=settings.groq_api_key)

async def transcribe_voice_note(media_url: str) -> str:
    """
    Downloads audio from Twilio and transcribes via Groq Whisper.
    """
    try:
        auth = (settings.twilio_account_sid, settings.twilio_auth_token)
        async with httpx.AsyncClient() as client:
            resp = await client.get(media_url, auth=auth)
            resp.raise_for_status()
            audio_bytes = resp.content

        # Groq Whisper large-v3 requires a file-like object
        # Using a tuple (filename, bytes)
        transcription = await _client.audio.transcriptions.create(
            file=("audio.ogg", audio_bytes),
            model="whisper-large-v3",
            response_format="text"
        )
        return transcription.strip()
    except Exception as e:
        logger.error(f"Voice transcription failed: {e}")
        return None
