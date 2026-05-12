def detect_intent(message: str) -> str:
    msg = message.lower().strip()

    intents = {
        "greeting": ["hi", "hello", "hey", "start", "begin"],
        "balance": ["balance", "how much", "my money", "kolo", "accounts", "check"],
        "withdraw": ["withdraw", "cash out", "i need money", "send to my account", "abeg send"],
        "pay": ["pay", "send money", "transfer", "settle", "buy from"],
        "add_supplier": ["add supplier", "new supplier", "save supplier", "save contact"],
        "summary": ["summary", "report", "how far", "how i dey", "my report", "analytics"],
        "score": ["score", "credit", "passport", "my score", "rating", "grade"],
        "help": ["help", "problem", "issue", "complaint", "useless", "scam", "human", "person"],
    }

    for intent, keywords in intents.items():
        if any(keyword in msg for keyword in keywords):
            return intent
    return "unknown"
