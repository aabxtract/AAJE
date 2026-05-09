FRUSTRATION_SIGNALS = {
    "en": [
        "scam", "fraud", "useless", "my money",
        "where is my money", "nonsense", "rubbish",
        "419", "thief", "steal", "robbery"
    ],
    "yo": [
        "jẹ́bú", "ole", "owo mi", "eyi o dara",
        "ẹ jẹ mi", "mo fẹ owo mi"
    ],
    "ig": [
        "aghụghọ", "ego m", "nzuzu", "ọ dịghị mma"
    ],
    "ha": [
        "zamba", "kuɗina", "banza", "kuturu"
    ],
    "pcm": [
        "scam", "419", "my money", "una don thief",
        "una dey use my money play", "this thing no work"
    ]
}

def detect_frustration(message: str, language: str = "en") -> bool:
    msg = message.lower()
    signals = FRUSTRATION_SIGNALS.get(language, [])
    signals += FRUSTRATION_SIGNALS["en"]  # always check English

    return any(signal in msg for signal in signals)

def detect_repeated_intent(session: dict, intent: str) -> bool:
    history = session.get("intent_history", [])
    history.append(intent)
    # Keep last 5 intents
    session["intent_history"] = history[-5:]

    # If same intent 3 times in last 5 messages
    if history.count(intent) >= 3:
        return True
    return False
