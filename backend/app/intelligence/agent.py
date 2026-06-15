"""The WhatsApp agent loop — CLAUDE.md §7 (System 2), Approach C.

Two LLM calls per inbound message:
1. Tool selection (3s timeout → keyword fallback)
2. Response generation using tool result (2s timeout → format result directly)

PII scrubbing runs before every LLM call. Tools never raise out.
The webhook handler is shielded from any exception by the outer try/except.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.context_builder import build_context
from app.intelligence.knowledge import detect_intent_for_knowledge, get_knowledge_for
from app.intelligence.llm_client import get_llm
from app.intelligence.tools import TOOL_DEFINITIONS, execute_tool
from app.models.user import User
from app.utils.formatters import format_naira
from app.utils.pii_scrubber import scrub

logger = logging.getLogger(__name__)

LLM_CALL_1_TIMEOUT_S = 3.0
LLM_CALL_2_TIMEOUT_S = 2.0


# ── Public entrypoint ────────────────────────────────────────────────────────
async def run_agent(
    message: str, *, db: AsyncSession, user: User, language: str = "en"
) -> str:
    """Run the full agent loop for one inbound message. Returns reply text.

    Never raises. On total failure, returns a safe fallback message in the
    trader's language.
    """
    started = time.monotonic()
    try:
        context = await build_context(db, user)
        scrubbed_context = scrub(context)

        # --- LLM Call 1: tool selection ---
        tool_call = await _select_tool(message, scrubbed_context)

        # --- Tool execution ---
        tool_name = None
        tool_result: dict | None = None
        if tool_call:
            tool_name = tool_call.get("name")
            try:
                arguments = json.loads(tool_call.get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            tool_result = await execute_tool(tool_name, arguments, db=db, user=user)

        # --- LLM Call 2: response generation ---
        reply = await _generate_response(
            message=message,
            scrubbed_context=scrubbed_context,
            tool_name=tool_name,
            tool_result=tool_result,
            language=language,
        )

        elapsed = time.monotonic() - started
        if elapsed > 5.0:
            logger.warning(
                "Agent loop slow path: %.2fs (tool=%s)", elapsed, tool_name
            )
        else:
            logger.info("Agent loop: %.2fs (tool=%s)", elapsed, tool_name)
        return reply
    except Exception:
        logger.exception("Agent loop failed entirely")
        return _safe_fallback(language)


# ── LLM Call 1: tool selection ───────────────────────────────────────────────
_TOOL_SELECT_SYSTEM = """You are AAJE's tool router. Given a Nigerian trader's WhatsApp message and their current context, decide which single tool (if any) to call.

Available tools have been provided via the tools API. Rules:
- Call exactly ONE tool when the trader's intent matches one clearly.
- If the message is a greeting, thanks, or vague question, call NO tool — just return without tool calls.
- Always extract specific values (product name, price, amount) from the message when calling tools that need them.
- Output ONLY the tool call. No explanatory text."""


async def _select_tool(message: str, scrubbed_context: dict) -> Optional[dict]:
    """Return a tool call dict ``{name, arguments}`` or None."""
    try:
        llm = get_llm()
    except Exception:
        return _keyword_fallback(message)

    try:
        response = await asyncio.wait_for(
            llm.complete(
                system=_TOOL_SELECT_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Trader context:\n{json.dumps(scrubbed_context)[:1500]}\n\n"
                            f"Trader message: {message}"
                        ),
                    }
                ],
                tools=TOOL_DEFINITIONS,
                temperature=0.0,
                max_tokens=300,
            ),
            timeout=LLM_CALL_1_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        logger.warning("LLM call 1 timed out — using keyword fallback")
        return _keyword_fallback(message)
    except Exception:
        logger.exception("LLM call 1 failed — using keyword fallback")
        return _keyword_fallback(message)

    tool_calls = response.get("tool_calls") or []
    if not tool_calls:
        return None
    return tool_calls[0]


def _keyword_fallback(message: str) -> Optional[dict]:
    """Cheap keyword-based intent routing for LLM-call-1 failures."""
    text = (message or "").lower().strip()
    if not text:
        return None

    if any(k in text for k in ("balance", "wallet", "how much", "earnings")):
        return {"name": "get_wallet_balance", "arguments": "{}"}
    if any(k in text for k in ("bizprint", "score", "credit", "loan")):
        return {"name": "get_bizprint", "arguments": "{}"}
    if any(k in text for k in ("my orders", "show orders", "orders", "pending order")):
        status = "pending" if "pending" in text else "all"
        return {"name": "get_orders", "arguments": json.dumps({"status": status, "limit": 5})}
    if any(k in text for k in ("store link", "my store", "share link", "share my store")):
        return {"name": "get_store_link", "arguments": "{}"}
    if any(k in text for k in ("summary", "performance", "how is business", "how far")):
        return {"name": "get_store_summary", "arguments": "{}"}
    if "withdraw" in text or "cash out" in text or "payout" in text:
        return {"name": "initiate_withdrawal", "arguments": "{}"}
    if text.startswith("add ") or "new product" in text or "create product" in text:
        return _parse_add_product(text)
    return None


def _parse_add_product(text: str) -> Optional[dict]:
    """Cheap extraction: 'add ankara bag 3500' → name+price."""
    import re

    cleaned = re.sub(r"^(add|create|new)\s+(product\s+)?", "", text, flags=re.IGNORECASE).strip()
    if not cleaned:
        return None
    # Find the last number in the cleaned text — that's the price
    numbers = re.findall(r"\d+(?:[.,]\d+)?", cleaned.replace("₦", "").replace("ngn", ""))
    if not numbers:
        return None
    price_str = numbers[-1].replace(",", "")
    try:
        price = float(price_str)
    except ValueError:
        return None
    if price <= 0:
        return None
    # Name = everything before the last number
    name_part = cleaned.rsplit(numbers[-1], 1)[0].strip(" :,-")
    if not name_part:
        return None
    name = " ".join(w.capitalize() for w in name_part.split())
    return {
        "name": "add_product",
        "arguments": json.dumps({"name": name, "price": price}),
    }


# ── LLM Call 2: response generation ──────────────────────────────────────────
_AGENT_SYSTEM_PROMPT_TEMPLATE = """You are AAJE, a business assistant for Nigerian traders and store owners.
You help them manage their store, track orders, understand their finances,
and grow their business.

CHARACTER:
- Direct and practical. No fluff. No unnecessary words.
- Warm but efficient. Like a trusted business partner who knows their situation.
- You understand Nigerian market context, informal business culture,
  and the reality of running a small business in Nigeria.
- You never talk down to traders. You respect their hustle.

STRICT SCOPE — you ONLY discuss:
- Their store: products, orders, customers, store link
- Their money: wallet balance, payments received, withdrawals
- Their BizPrint score and what it means for their business
- AAJE features and how to use them
- Nigerian business context directly relevant to their store
  (pricing trends, market advice, business growth)

OUT OF SCOPE — if the message is not about their business or AAJE,
respond with EXACTLY this and nothing else:
"I only help with your store and business.
Ask me about your orders, balance, or BizPrint."

LANGUAGE RULES:
- Respond ONLY in {language_name}
- Yoruba: respectful, warm, use honorifics naturally
- Pidgin: casual, energetic, trusted friend tone
- Igbo: direct, progress-focused, use Oganiru for progress
- Hausa: community-oriented, trust-building tone
- English: direct, clear, no jargon
- NEVER mix languages unless the trader does first

CURRENT TRADER CONTEXT:
{scrubbed_context}

AAJE KNOWLEDGE FOR THIS CONVERSATION:
{relevant_knowledge}

TOOL RESULT:
{tool_result}

STRICT RULES:
- Never make up numbers. Use ONLY numbers from the context above.
- Never promise loans or guarantee financial outcomes.
- Never discuss other businesses, apps, or platforms by name.
- Keep responses under 150 words unless showing a list of orders or products.
- For lists: show maximum 5 items then say "Type 'more' to see the rest."
- Always end money-related responses with the current wallet balance.
- If something went wrong: be honest, explain simply, tell them what to do next."""


_LANGUAGE_NAMES = {
    "en": "English",
    "yo": "Yoruba",
    "ig": "Igbo",
    "ha": "Hausa",
    "pcm": "Nigerian Pidgin",
}


async def _generate_response(
    *,
    message: str,
    scrubbed_context: dict,
    tool_name: Optional[str],
    tool_result: Optional[dict],
    language: str,
) -> str:
    """Run LLM Call 2. On timeout/failure, format the tool result directly."""
    knowledge = get_knowledge_for(detect_intent_for_knowledge(message))
    language_name = _LANGUAGE_NAMES.get(language, "English")

    scrubbed_tool_result = scrub(tool_result) if isinstance(tool_result, dict) else None

    system = _AGENT_SYSTEM_PROMPT_TEMPLATE.format(
        language_name=language_name,
        scrubbed_context=json.dumps(scrubbed_context)[:1500],
        relevant_knowledge=knowledge,
        tool_result=(
            json.dumps(scrubbed_tool_result) if scrubbed_tool_result is not None else "none"
        ),
    )

    try:
        llm = get_llm()
        response = await asyncio.wait_for(
            llm.complete(
                system=system,
                messages=[{"role": "user", "content": message}],
                temperature=0.3,
                max_tokens=400,
            ),
            timeout=LLM_CALL_2_TIMEOUT_S,
        )
        content = (response.get("content") or "").strip()
        if content:
            return content
    except asyncio.TimeoutError:
        logger.warning("LLM call 2 timed out — formatting tool result directly")
    except Exception:
        logger.exception("LLM call 2 failed — formatting tool result directly")

    return _format_tool_result_directly(tool_name, tool_result, scrubbed_context)


# ── Direct formatters (LLM-free fallbacks) ───────────────────────────────────
def _format_tool_result_directly(
    tool_name: Optional[str], result: Optional[dict], context: dict
) -> str:
    """Render a tool result as plain text without an LLM call."""
    if result is None and tool_name is None:
        return _safe_fallback(context.get("trader", {}).get("language", "en"))

    if not isinstance(result, dict):
        return "I got your message. Type *menu* to see what AAJE can do."

    if result.get("error"):
        return result.get("message") or "Something went wrong. Please try again."

    if tool_name == "get_wallet_balance":
        bal = result.get("available_balance", 0)
        earned = result.get("total_earned", 0)
        return (
            f"💰 Wallet balance: {format_naira(bal)}\n"
            f"Total earned: {format_naira(earned)}"
        )

    if tool_name == "get_store_summary":
        return (
            f"📊 Today at {result.get('store_name', 'your store')}:\n"
            f"- Orders today: {result.get('today_orders', 0)}\n"
            f"- Revenue today: {format_naira(result.get('today_revenue', 0))}\n"
            f"- Pending: {result.get('pending_orders', 0)}\n"
            + (f"- Top product: {result['top_product']}" if result.get("top_product") else "")
        )

    if tool_name == "get_orders":
        orders = result.get("orders") or []
        if not orders:
            return "No orders to show yet."
        lines = ["📦 Your orders:"]
        for o in orders[:5]:
            lines.append(
                f"- {o['order_ref']} — {o['customer_name']} — "
                f"{format_naira(o['amount'])} — {o['status']}"
            )
        if len(orders) > 5:
            lines.append("Type 'more' to see the rest.")
        return "\n".join(lines)

    if tool_name == "add_product":
        if result.get("ok"):
            p = result.get("product") or {}
            return (
                f"✅ {p.get('name', 'Product')} added at "
                f"{format_naira(p.get('price', 0))}. Your store is updated."
            )
        return result.get("message") or (
            "Adding products from chat is coming soon. Use your dashboard for now."
        )

    if tool_name == "get_bizprint":
        if not result.get("available"):
            return result.get("message") or "BizPrint not yet computed."
        return (
            f"📊 BizPrint: {result.get('score', 0):.1f} ({result.get('grade', '—')})\n"
            f"Loan ceiling: {format_naira(result.get('loan_ceiling', 0))}\n"
            f"Orders analyzed: {result.get('orders_analyzed', 0)}"
        )

    if tool_name == "initiate_withdrawal":
        if not result.get("ok"):
            return result.get("message") or "Could not start withdrawal."
        bal = result.get("available_balance", 0)
        return (
            f"💸 Withdrawal: available balance is {format_naira(bal)}.\n"
            f"{result.get('message', '')}"
        )

    if tool_name == "get_store_link":
        return result.get("share_message") or result.get("url") or "Store link unavailable."

    return "I got your message. Type *menu* to see what AAJE can do."


def _safe_fallback(language: str) -> str:
    """Last-resort reply when everything fails."""
    fallbacks = {
        "en": "I'm having trouble right now. Please try again in a moment.",
        "yo": "Mo ní wàhálà bàyìí. Jọ̀wọ́ gbìyànjú lẹ́yìn ìṣẹ́jú méjì.",
        "ig": "Enwere m nsogbu ugbu a. Biko nwaa ọzọ obere oge.",
        "ha": "Ina da matsala yanzu. Don Allah a sake gwadawa.",
        "pcm": "I dey get small wahala now. Try again small time.",
    }
    return fallbacks.get(language, fallbacks["en"])
