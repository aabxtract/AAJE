def detect_intent(message: str, language: str = "en") -> str:
    msg = message.lower().strip()

    INTENTS = {
        "greeting": [
            "hi", "hello", "hey", "start", "begin",
            "ẹ káàbọ̀", "ndewo", "sannu", "how far",
            "wetin dey"
        ],
        "summary": [
            "summary", "report", "how far", "how i dey",
            "wetin happen", "my report", "analytics",
            "show me", "business"
        ],
        "vault_balance": [
            "balance", "kolo", "vault", "savings",
            "how much", "my money", "check"
        ],
        "withdraw": [
            "withdraw", "cash out", "send to my account",
            "i need money", "owo", "give me my money",
            "abeg send"
        ],
        "pay_supplier": [
            "pay", "send money", "transfer", "buy from",
            "settle"
        ],
        "add_supplier": [
            "add supplier", "new supplier", "save supplier",
            "add contact", "new contact"
        ],
        "move_vault": [
            "move", "shift", "transfer between",
            "move from", "shift money"
        ],
        "change_language": [
            "yoruba", "igbo", "hausa", "pidgin",
            "english", "change language", "switch language"
        ],
        "change_pin": [
            "change pin", "forgot pin", "reset pin",
            "pin reset", "new pin"
        ],
        "help": [
            "help", "human", "speak to someone",
            "i have problem", "support", "issue",
            "complaint", "useless", "scam"
        ],
        "trader_score": [
            "score", "credit score", "passport",
            "my score", "rating"
        ],
    }

    for intent, keywords in INTENTS.items():
        if any(kw in msg for kw in keywords):
            return intent

    return "unknown"
