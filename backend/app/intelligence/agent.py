import json
import logging
import re

from app.intelligence.llm import _get_client, MODEL

logger = logging.getLogger(__name__)

ALLOWED_TOPICS = {
    "store", "business", "inventory", "sales", "payment", "payments", "savings",
    "vault", "vaults", "score", "bizprint", "order", "orders", "withdraw",
    "withdrawal", "money", "account", "receipt", "report", "stock", "product",
}


def _guardrail_reject(message: str) -> bool:
    text = message.lower()
    if text.startswith("system_event:"):
        return False
    if any(topic in text for topic in ALLOWED_TOPICS):
        return False
    greetings = {"hi", "hello", "hey", "help", "menu", "start"}
    return text.strip() not in greetings


def _amount_from_text(message: str) -> float | None:
    normalized = message.lower().replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", normalized)
    if match:
        return float(match.group(1)) * 1000
    match = re.search(r"(\d+(?:\.\d+)?)", normalized)
    return float(match.group(1)) if match else None


async def agent_reason(event, context, available_tools):
    """
    Return JSON:
    {
      "persona": "storefront_extension | normal_business_manager",
      "intent": "...",
      "tools_to_call": ["..."],
      "response": "...",
      "requires_flow": true/false,
      "flow_type": "...",
      "requires_pin": true/false,
      "proactive_flags": []
    }
    """
    message = str(event or "")
    persona = context.get("persona", "normal_business_manager")
    if _guardrail_reject(message):
        return {
            "persona": persona,
            "intent": "rejected_unrelated",
            "tools_to_call": [],
            "response": "AAJE only helps with your business, store, payments, savings, score, and financial records.",
            "requires_flow": False,
            "flow_type": None,
            "requires_pin": False,
            "proactive_flags": [],
        }

    fallback = _rule_based_reason(message, context)
    client = _get_client()
    if not client:
        return fallback

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Squad Intelligence for AAJE. Return only valid JSON matching the requested schema. "
                        "Use tools only from the provided list. Never approve money movement without PIN. "
                        "Reject unrelated topics with the exact AAJE guardrail sentence."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Event/message: {message}\nContext: {context}\nTools: {available_tools}\n"
                        "Schema keys: persona, intent, tools_to_call, response, requires_flow, flow_type, requires_pin, proactive_flags."
                    ),
                },
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=600,
        )
        data = json.loads(response.choices[0].message.content)
        data.setdefault("persona", persona)
        data.setdefault("tools_to_call", [])
        data.setdefault("requires_flow", False)
        data.setdefault("requires_pin", False)
        data.setdefault("proactive_flags", [])
        return data
    except Exception:
        logger.exception("Persona-aware agent reasoning failed; using rules")
        return fallback


def _rule_based_reason(message: str, context: dict) -> dict:
    text = message.lower()
    persona = context.get("persona", "normal_business_manager")
    store = context.get("store")
    if "withdraw" in text:
        amount = _amount_from_text(text)
        return {
            "persona": persona,
            "intent": "withdrawal",
            "tools_to_call": [{"name": "initiate_withdrawal", "kwargs": {"amount": amount or 0}}],
            "response": "I will open a secure withdrawal flow. No money leaves AAJE without your PIN.",
            "requires_flow": True,
            "flow_type": "withdrawal",
            "requires_pin": True,
            "proactive_flags": [],
        }
    if persona == "storefront_extension":
        if "sold today" in text or "sales today" in text or "today" in text:
            return _answer("today_sales", "generate_store_insight", "I am checking today's store sales now.")
        if "low" in text and ("stock" in text or "inventory" in text):
            low = context.get("recent_alerts") or []
            names = ", ".join(item["product"] for item in low) or "none"
            return _plain(persona, "low_stock", f"Low-stock products: {names}.")
        if "store link" in text or "send my store" in text:
            link = store.get("link") if store else None
            return _plain(persona, "store_link", f"Your store link is {link}." if link else "You do not have a connected store yet.")
        if "pending order" in text:
            pending = [o for o in context.get("orders", []) if o["payment_status"] != "paid"]
            return _plain(persona, "pending_orders", f"You have {len(pending)} pending order(s).")
        if "fastest" in text or "top product" in text:
            return _answer("top_products", "get_top_products", "I am checking your fastest moving products.")
        return _plain(persona, "storefront_help", "You can ask about sales, pending orders, low stock, store link, withdrawals, vaults, score, and BizPrint.")

    if "score" in text:
        score = context.get("score") or {}
        return _plain(persona, "score", f"Your current score is {score.get('score', 0)} with grade {score.get('grade') or 'not ready yet'}.")
    if "bizprint" in text:
        return _answer("bizprint", "get_bizprint", "I am pulling your BizPrint.")
    if "balance" in text or "vault" in text:
        wallet = context.get("wallet") or {}
        if wallet:
            return _plain(persona, "wallet_balance", f"Your available wallet balance is NGN {wallet.get('available_balance', 0):,.2f}. Total earned: NGN {wallet.get('total_earned', 0):,.2f}.")
        vaults = context.get("vaults") or []
        if not vaults:
            return _plain(persona, "vault_balances", "You do not have vault balances yet.")
        lines = [f"{v['name']}: NGN {v['balance']:,.2f}" for v in vaults]
        return _plain(persona, "vault_balances", "\n".join(lines))
    return _plain(persona, "business_help", "You can ask about balances, vaults, payments, withdrawals, score, receipts, reports, and BizPrint.")


def _plain(persona: str, intent: str, response: str) -> dict:
    return {"persona": persona, "intent": intent, "tools_to_call": [], "response": response, "requires_flow": False, "flow_type": None, "requires_pin": False, "proactive_flags": []}


def _answer(intent: str, tool: str, response: str) -> dict:
    return {"persona": "storefront_extension", "intent": intent, "tools_to_call": [{"name": tool, "kwargs": {}}], "response": response, "requires_flow": False, "flow_type": None, "requires_pin": False, "proactive_flags": []}
