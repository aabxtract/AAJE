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

_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
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
