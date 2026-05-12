import logging
from typing import Optional

from groq import AsyncGroq

from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=settings.groq_api_key)
MODEL = "openai/gpt-oss-120b"


def _get_client() -> Optional[AsyncGroq]:
    global client
    if client is None:
        key = getattr(settings, "groq_api_key", None)
        if not key:
            return None
        try:
            client = AsyncGroq(api_key=key)
        except Exception:
            logger.exception("Failed to initialize Groq client")
            client = None
    return client


async def categorize_transaction(narration: str, stream_names: list[str]) -> str:
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial categorization engine for a Nigerian trader. "
                        "Given this payment narration and the trader's business names, return only "
                        "the business name that this payment most likely belongs to. If unclear, "
                        "return the first business name. Return only the business name, nothing else."
                    ),
                },
                {"role": "user", "content": f"Narration: {narration}. Business names: {stream_names}"},
            ],
            temperature=0,
            max_tokens=50,
        )
        selected = response.choices[0].message.content.strip()
        return selected if selected in stream_names else stream_names[0]
    except Exception:
        logger.exception("Transaction categorization failed")
        return stream_names[0]


async def translate_message(text: str, language: str) -> str:
    if language == "en":
        return text
    language_map = {
        "yo": ("Yoruba", "respectful warm tone"),
        "ig": ("Igbo", "growth-focused tone"),
        "ha": ("Hausa", "community trust tone"),
        "pcm": ("Nigerian Pidgin", "casual friendly tone"),
    }
    target = language_map.get(language)
    if not target:
        return text
    c = _get_client()
    if not c:
        # No API key available — fallback to English text to avoid crashing.
        logger.warning("Groq client unavailable; returning English fallback for translation to %s", language)
        return text
    language_name, tone = target
    try:
        response = await c.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Translate into {language_name}. Use a {tone}. "
                        "For non-English languages, do not include English in the output. "
                        "Return only the translated message."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.exception("Translation failed for language %s", language)
        return text


async def generate_insight(scrubbed_context: dict) -> str:
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial advisor for a Nigerian market trader. "
                        "Be direct and specific. Maximum 2 sentences. Use only the numbers provided. "
                        "End with one concrete action."
                    ),
                },
                {"role": "user", "content": str(scrubbed_context)},
            ],
            temperature=0.3,
            max_tokens=160,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.exception("Insight generation failed")
        return "Keep track of your daily sales to grow your business score."
