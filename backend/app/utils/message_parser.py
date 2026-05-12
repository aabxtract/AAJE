"""
Message intent detection for the WhatsApp session router.
Supports English, Yoruba, Igbo, Hausa, and Nigerian Pidgin keywords.
"""


def detect_intent(message: str) -> str:
    msg = message.lower().strip()

    # Ordered by specificity — more specific intents first
    intents = {
        "add_supplier": [
            "add supplier", "new supplier", "save supplier", "save contact",
        ],
        "debrief": [
            "debrief", "daily report", "today report", "how today go",
            "my day", "end of day", "report today",
        ],
        "score": [
            "score", "credit", "passport", "my score", "rating", "grade",
            "credit score", "economic identity",
        ],
        "summary": [
            "summary", "report", "how far", "how i dey", "my report",
            "analytics", "how business", "business report",
        ],
        "withdraw": [
            "withdraw", "cash out", "i need money", "send to my account",
            "abeg send", "send money to me", "take out",
        ],
        "pay": [
            "pay", "send money", "transfer", "settle", "buy from",
            "pay supplier", "pay vendor",
        ],
        "balance": [
            "balance", "how much", "my money", "kolo", "accounts", "check",
            "vault", "owo mi", "ego m", "kudi na", "wetin remain",
        ],
        "support": [
            "human", "person", "speak to someone", "real person", "agent",
            "talk to someone", "customer care", "customer service",
        ],
        "help": [
            "help", "menu", "what can you do", "options", "wetin you fit do",
        ],
        "greeting": [
            "hi", "hello", "hey", "start", "begin", "good morning",
            "good afternoon", "good evening", "e kaaro", "ndewo",
            "sannu", "how far",
        ],
    }

    for intent, keywords in intents.items():
        if any(keyword in msg for keyword in keywords):
            return intent
    return "unknown"
