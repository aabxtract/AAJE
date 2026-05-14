import logging
from typing import Optional

from groq import AsyncGroq

from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=settings.groq_api_key)
MODEL = "openai/gpt-oss-120b"

STATIC_TRANSLATIONS = {
    "What is your full name?\nExample: Adebayo Olusegun Okonkwo": {
        "yo": "Kí ni orúkọ rẹ pátápátá?\nÀpẹẹrẹ: Adebayo Olusegun Okonkwo",
        "ig": "Kedu aha gị zuru ezu?\nIhe atụ: Adebayo Olusegun Okonkwo",
        "ha": "Menene cikakken sunanka?\nMisali: Adebayo Olusegun Okonkwo",
        "pcm": "Wetin be your full name?\nExample: Adebayo Olusegun Okonkwo",
    },
    "What is your full name?": {
        "yo": "Kí ni orúkọ rẹ pátápátá?",
        "ig": "Kedu aha gị zuru ezu?",
        "ha": "Menene cikakken sunanka?",
        "pcm": "Wetin be your full name?",
    },
    "What market or town do you trade in?": {
        "yo": "Ọjà tàbí ìlú wo ni o ti ń ṣòwò?",
        "ig": "Kedu ahịa ma ọ bụ obodo ị na-azụ ahịa na ya?",
        "ha": "A wane kasuwa ko gari kake/kike kasuwanci?",
        "pcm": "Which market or town you dey sell for?",
    },
    "Please reply with 1, 2, 3, 4, or 5.": {
        "yo": "Jọ̀wọ́ dáhùn pẹ̀lú 1, 2, 3, 4, tàbí 5.",
        "ig": "Biko zaa na 1, 2, 3, 4, ma ọ bụ 5.",
        "ha": "Don Allah ka/kika amsa da 1, 2, 3, 4, ko 5.",
        "pcm": "Abeg reply with 1, 2, 3, 4, or 5.",
    },
    "Creating your Squad accounts now...": {
        "yo": "A ń dá àwọn àkọọlẹ Squad rẹ sílẹ̀ báyìí...",
        "ig": "Anyị na-emepụta akaụntụ Squad gị ugbu a...",
        "ha": "Muna ƙirƙirar asusun Squad ɗinka yanzu...",
        "pcm": "We dey create your Squad accounts now...",
    },
}


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
    language = (language or "en").lower()
    if not text or language == "en":
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
    static = STATIC_TRANSLATIONS.get(text, {}).get(language)
    if static:
        return static
    c = _get_client()
    if not c:
        # No API key available — fallback to English text to avoid crashing.
        logger.warning("Groq client unavailable; returning English fallback for translation to %s", language)
        return static or text
    language_name, tone = target
    try:
        response = await c.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional translator. Translate the given text into {language_name}. "
                        f"Use a {tone}. Do not add any explanations, prefixes, or notes. "
                        "Return ONLY the translated text. If you cannot translate it, return the original text."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        translated = response.choices[0].message.content.strip()
        if not translated:
            logger.warning("LLM returned empty translation for %s", language)
            return static or text
        return translated
    except Exception:
        logger.exception("Translation failed for language %s", language)
        return static or text


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


async def agent_reason(message: str, context: dict, available_tools: list[str]) -> dict:
    """
    Main brain for the agentic flow. Decides what to do, what tools to call,
    what matters, and what response to generate based on user state and input.
    """
    c = _get_client()
    if not c:
        return {
            "reasoning": "LLM client unavailable.",
            "tools_to_call": [],
            "response": "I'm currently unable to process your request due to a connection issue.",
            "proactive_flags": []
        }

    system_prompt = """You are AAJE's storefront operations assistant on WhatsApp.
The storefront is the main product. WhatsApp is a reactive operations layer for storefront activity.
You help with orders, inventory, sales, withdrawals, campaign performance, and BizPrint insights.

IMPORTANT IMPLEMENTATION RULES:
1. NEVER move money automatically; withdrawals must use a secure browser flow and PIN.
2. NEVER invent numbers.
3. Keep responses concise, operational, and business-oriented.
4. Do not behave like a generic banking assistant, finance chatbot, or AI companion.

You are given the user's message (or system event), their storefront context, and a list of available tools.
You MUST output ONLY valid JSON in the following format:
{
  "reasoning": "your internal monologue about what the user needs and what to do",
  "tools_to_call": [{"name": "tool_name", "kwargs": {"arg1": "val1"}}],
  "response": "your textual response to the user, if any (leave empty if just calling tools or no response needed yet)",
  "proactive_flags": ["list of strings representing proactive insights"]
}

Available Tool Information:
- `get_recent_orders()`, `get_pending_orders()`, `get_today_sales()`
- `get_low_stock_products()`, `update_inventory_from_chat()`, `create_product_from_chat_message()`
- `get_top_products()`, `get_marketing_analytics_tool()`, `get_bizprint()`
- `initiate_withdrawal(amount: float)`: Creates a secure browser flow for PIN confirmation.
"""
    try:
        response = await c.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Message/Event: {message}\n\nContext: {context}\n\nAvailable Tools: {available_tools}"},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=800,
        )
        content = response.choices[0].message.content.strip()
        import json
        result = json.loads(content)
        return result
    except Exception:
        logger.exception("Agent reasoning failed")
        return {
            "reasoning": "Error occurred during reasoning.",
            "tools_to_call": [],
            "response": "I am having trouble thinking right now. Please try again later.",
            "proactive_flags": []
        }
