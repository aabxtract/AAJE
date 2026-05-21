_IN_SCOPE_KEYWORDS = {
    # Greetings / navigation
    "hi", "hello", "hey", "start", "menu", "help",
    # Store & products
    "store", "shop", "product", "products", "stock", "inventory", "item", "items",
    "add product", "update", "price",
    # Orders & sales
    "order", "orders", "sale", "sales", "sold", "customer", "customers",
    "pending", "fulfilled", "delivered",
    # Financial
    "balance", "wallet", "withdraw", "withdrawal", "payment", "paid", "payout",
    "money", "naira", "ngn", "₦", "earn", "earning", "revenue", "profit",
    # BizPrint
    "bizprint", "score", "loan", "credit", "business",
    # AAJE
    "aaje", "dashboard", "storefront", "link", "my link",
}

_OFF_TOPIC = (
    "AAJE is your business operating system. I can only help with:\n\n"
    "- Store & product management\n"
    "- Orders and sales\n"
    "- Wallet balance and withdrawals\n"
    "- BizPrint business score\n\n"
    "Type *help* to see available commands."
)


def is_in_scope(message: str) -> bool:
    text = message.lower()
    return any(kw in text for kw in _IN_SCOPE_KEYWORDS)


def off_topic_response() -> str:
    return _OFF_TOPIC
