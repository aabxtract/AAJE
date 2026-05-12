FRUSTRATION_SIGNALS = [
    "scam", "fraud", "useless", "nonsense", "rubbish", "419", "thief",
    "steal", "where is my money", "my money", "complaint", "human",
    "person", "ole", "owo mi", "e je mi", "ego m", "zamba", "banza",
    "una don thief", "this thing no work", "abeg help", "wahala",
]


def detect_frustration(message: str) -> bool:
    msg = message.lower()
    return any(signal in msg for signal in FRUSTRATION_SIGNALS)
