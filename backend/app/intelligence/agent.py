import json
import logging
import re

from app.intelligence.llm import _get_client, MODEL

logger = logging.getLogger(__name__)

ALLOWED_TOPICS = {
    "store", "storefront", "business", "inventory", "sales", "payment", "payments",
    "payout", "payouts", "bizprint", "order", "orders", "withdraw",
    "withdrawal", "receipt", "report", "stock", "product", "products",
    "sold", "pending", "link", "analytics", "revenue", "checkout",
    "customer", "customers", "fulfilled", "delivered", "summary",
    "campaign", "campaigns", "marketing", "growth", "source", "sources",
    "referral", "referrals", "instagram", "whatsapp", "facebook", "tiktok",
}


def _guardrail_reject(message: str) -> bool:
    text = message.lower()
    if text.startswith("system_event:"):
        return False
    if "today" in text and any(topic in text for topic in {"sold", "sales", "orders", "payment", "revenue", "income"}):
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
      "persona": "storefront_operations",
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
    persona = context.get("persona", "storefront_operations")
    if _guardrail_reject(message):
        return {
            "persona": persona,
            "intent": "rejected_unrelated",
            "tools_to_call": [],
            "response": "AAJE WhatsApp only helps with storefront operations: orders, inventory, sales, withdrawals, campaigns, and BizPrint.",
            "requires_flow": False,
            "flow_type": None,
            "requires_pin": False,
            "proactive_flags": [],
        }

    fallback = _rule_based_reason(message, context)
    if fallback.get("intent") not in {"storefront_help", "business_help"} or str(message).lower().strip() in {"help", "menu", "start", "hi", "hello"}:
        return fallback
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
                        "You are AAJE's storefront operations assistant on WhatsApp. "
                        "The storefront is the main product; WhatsApp is reactive and operational. "
                        "Return only valid JSON matching the requested schema. Use tools only from the provided list. "
                        "Focus on orders, inventory, sales, withdrawals, campaigns, and BizPrint. "
                        "Never act like a bank, generic finance bot, AI companion, or payment-first assistant. "
                        "Never approve money movement without a secure browser flow and PIN. "
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
    persona = context.get("persona", "storefront_operations")
    tier = (context.get("whatsapp") or {}).get("tier", "free")
    store = context.get("store")
    words = set(re.findall(r"[a-z0-9']+", text))
    is_help = bool(words & {"help", "menu", "start", "hello", "hi"}) or "what can you do" in text

    if tier != "premium":
        if "store link" in text or "send my store" in text or "link" == text.strip():
            link = store.get("link") if store else None
            return _plain(persona, "store_link", f"Your store link is {link}." if link else "You do not have a connected store yet.")
        if is_help:
            return _plain(
                persona,
                "free_whatsapp_help",
                "Free WhatsApp is enabled for order/payment alerts, daily sales summaries, and store link sharing. Upgrade to Premium for operational chat: sales questions, inventory updates, order management, withdrawals, campaign analytics, and BizPrint insights.",
            )
        return _plain(
            persona,
            "premium_required",
            "That WhatsApp operation is available on Premium. Free WhatsApp still sends order/payment alerts, daily summaries, and your store link.",
        )

    if is_help:
        return _plain(
            persona,
            "storefront_help",
            "Ask me about your storefront: store link, what sold today, recent orders, pending orders, low stock, update stock, mark order fulfilled, withdrawals, campaign performance, and BizPrint summary.",
        )

    if any(term in text for term in {"campaign", "marketing", "growth", "source", "sources", "referral", "instagram", "facebook", "tiktok"}) or (
        "where" in text and "customers" in text and "coming" in text
    ) or (
        "what brought" in text and ("sales" in text or "orders" in text)
    ):
        days = 1 if "today" in text else 7 if "week" in text else 30 if "month" in text else 7
        return {
            "persona": persona,
            "intent": "marketing_attribution",
            "tools_to_call": [{"name": "get_marketing_analytics_tool", "kwargs": {"days": days}}],
            "response": "I am checking your growth attribution now.",
            "requires_flow": False,
            "flow_type": None,
            "requires_pin": False,
            "proactive_flags": [],
        }
    if "withdraw" in text:
        amount = _amount_from_text(text)
        if not amount or amount <= 0:
            return _plain(persona, "withdrawal_amount_needed", "Send the withdrawal amount. Example: withdraw 25000.")
        return {
            "persona": persona,
            "intent": "withdrawal",
            "tools_to_call": [{"name": "initiate_withdrawal", "kwargs": {"amount": amount}}],
            "response": "I will open a secure withdrawal flow. No money leaves AAJE without your PIN.",
            "requires_flow": True,
            "flow_type": "withdrawal",
            "requires_pin": True,
            "proactive_flags": [],
        }
    if "payout" in text or "wallet" in text or ("balance" in text and "stock" not in text):
        wallet = context.get("wallet") or {}
        if wallet:
            return _plain(persona, "wallet_balance", f"Your available wallet balance is NGN {wallet.get('available_balance', 0):,.2f}. Total earned: NGN {wallet.get('total_earned', 0):,.2f}.")
        return _plain(persona, "wallet_balance", "Your storefront wallet is not ready yet.")
    if persona == "storefront_operations":
        if "sold today" in text or "sales today" in text or ("today" in text and any(term in text for term in {"sold", "sales", "orders", "revenue"})):
            return _answer("today_sales", "generate_store_insight", "I am checking today's store sales now.")
        if "recent order" in text or "latest order" in text:
            return _answer("recent_orders", "get_recent_orders", "I am checking your recent orders.")
        if "low" in text and ("stock" in text or "inventory" in text):
            return _answer("low_stock", "get_low_stock_products", "I am checking low-stock products.")
        if "store link" in text or "send my store" in text:
            link = store.get("link") if store else None
            return _plain(persona, "store_link", f"Your store link is {link}." if link else "You do not have a connected store yet.")
        if "pending order" in text:
            return _answer("pending_orders", "get_pending_orders", "I am checking pending orders.")
        if "fulfill" in text or "fulfilled" in text:
            return _answer("mark_order_fulfilled", "mark_order_fulfilled_from_chat", "I am checking that order.")
        if ("add" in text or "update" in text or "set" in text) and ("stock" in text or "inventory" in text):
            return _answer("update_inventory", "update_inventory_from_chat", "I am updating inventory from your message.")
        if "add product" in text or "new product" in text:
            return _answer("create_product", "create_product_from_chat_message", "I am creating that product from your message.")
        if "fastest" in text or "top product" in text or "best product" in text:
            return _answer("top_products", "get_top_products", "I am checking your fastest moving products.")
        if "bizprint" in text:
            return _answer("bizprint", "get_bizprint", "I am pulling your BizPrint summary.")
        return _plain(persona, "storefront_help", "Ask about store link, sales, recent orders, pending orders, low stock, stock updates, withdrawals, campaign performance, and BizPrint.")

    if "bizprint" in text:
        return _answer("bizprint", "get_bizprint", "I am pulling your BizPrint.")
    return _plain(persona, "business_help", "Connect a storefront from your dashboard to use WhatsApp operations.")


def _plain(persona: str, intent: str, response: str) -> dict:
    return {"persona": persona, "intent": intent, "tools_to_call": [], "response": response, "requires_flow": False, "flow_type": None, "requires_pin": False, "proactive_flags": []}


def _answer(intent: str, tool: str, response: str) -> dict:
    return {"persona": "storefront_operations", "intent": intent, "tools_to_call": [{"name": tool, "kwargs": {}}], "response": response, "requires_flow": False, "flow_type": None, "requires_pin": False, "proactive_flags": []}
