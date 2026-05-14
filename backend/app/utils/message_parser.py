"""
Lightweight intent detection for AAJE WhatsApp storefront operations.

Translation can support UX, but the product center is operational clarity:
orders, inventory, sales, withdrawals, campaigns, and BizPrint.
"""


def detect_intent(message: str) -> str:
    msg = message.lower().strip()

    intents = {
        "store_link": [
            "store link", "send my store", "share my store", "my link", "store url",
        ],
        "today_sales": [
            "what sold today", "sold today", "sales today", "today sales", "revenue today",
        ],
        "recent_orders": [
            "recent orders", "latest orders", "show orders", "orders",
        ],
        "pending_orders": [
            "pending orders", "unfulfilled orders", "orders pending",
        ],
        "mark_order_fulfilled": [
            "mark fulfilled", "mark order fulfilled", "fulfilled", "delivered",
        ],
        "low_stock": [
            "low stock", "low inventory", "what is low", "restock",
        ],
        "update_inventory": [
            "update stock", "add stock", "set stock", "update inventory", "add inventory",
        ],
        "add_product": [
            "add product", "new product", "create product",
        ],
        "withdraw": [
            "withdraw", "cash out", "payout", "send to my account",
        ],
        "campaign_performance": [
            "campaign", "campaign performance", "marketing", "growth", "source", "referral",
        ],
        "bizprint": [
            "bizprint", "business profile", "store profile",
        ],
        "support": [
            "human", "person", "speak to someone", "real person", "customer care",
        ],
        "help": [
            "help", "menu", "what can you do", "options",
        ],
        "greeting": [
            "hi", "hello", "hey", "start", "good morning", "good afternoon", "good evening",
        ],
    }

    for intent, keywords in intents.items():
        if any(keyword in msg for keyword in keywords):
            return intent
    return "unknown"
