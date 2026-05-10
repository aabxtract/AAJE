"""
Groq LLM service — Llama 4 Scout.

Used for:
  - Transaction categorization
  - Business insight generation
  - Daily debrief narrative
  - Dynamic split reasoning

Always receives pre-processed, structured context from refinery.py.
Never reasons on raw transaction data.
"""
import logging

from groq import AsyncGroq

from app.config import settings

logger = logging.getLogger(__name__)

_client = AsyncGroq(api_key=settings.groq_api_key)
_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

SYSTEM_PROMPT = """
You are AAJE, a trusted financial advisor for Nigerian market traders.
You communicate in simple, warm, direct language — like a smart friend who understands business.
You never use jargon. You always give concrete, actionable insights.
When given transaction data, you explain what it means in plain terms and what the trader should do next.
Keep responses short — this is WhatsApp, not a report.
""".strip()


async def categorize_transaction(description: str, amount: float) -> str:
    """Return a single category label for a transaction."""
    resp = await _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Categorize this transaction in one word or short phrase.\n"
                    f"Description: {description}\nAmount: ₦{amount:,.0f}\n"
                    f"Categories: Sales, Inventory, Transport, Food, Utilities, Transfer, Other"
                ),
            },
        ],
        max_tokens=20,
        temperature=0.1,
    )
    return resp.choices[0].message.content.strip()


async def generate_insight(context: dict) -> str:
    """Generate a daily debrief insight from refinery output."""
    resp = await _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Here is today's business summary for a trader:\n{context}\n\n"
                    f"Write a short WhatsApp message (3–5 sentences max) giving them "
                    f"their key insight and one practical tip for tomorrow."
                ),
            },
        ],
        max_tokens=200,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()

async def translate_to_language(english_insight: str, language_code: str) -> str:
    if language_code.lower() == "en":
        return english_insight
        
    language_map = {
        "yo": ("Yoruba", "respectful honorifics and warm tone"),
        "ig": ("Igbo", "growth-centric and progress-focused language"),
        "ha": ("Hausa", "community trust language"),
        "pcm": ("Nigerian Pidgin", "casual friendly energy")
    }
    
    lang_info = language_map.get(language_code.lower())
    if not lang_info:
        return english_insight
        
    target_language, tone_instruction = lang_info
    
    system_prompt = f"""
You are the AAJE Business Manager. 
Translate the provided English text into {target_language}.
Use colloquial, encouraging market-day terminology.
Tone required: {tone_instruction}.
CRITICAL RULE: DO NOT include any English words in the output. Translate EVERYTHING into {target_language}.
Return ONLY the translated text. No pleasantries. No intro.
""".strip()
    try:
        resp = await _client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": english_insight},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Translation to {target_language} failed: {e}")
        return english_insight

from app.utils.phrases import get_phrase, PHRASES

async def get_cached_or_translate(key_or_text: str, language_code: str) -> str:
    """
    Checks the phrase cache first. If found, returns the static string.
    If not found, assumes it's dynamic English text and translates it via LLM.
    """
    if key_or_text in PHRASES:
        return get_phrase(key_or_text, language_code)
    
    return await translate_to_language(key_or_text, language_code)
