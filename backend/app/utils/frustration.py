"""
Frustration detection — identifies when a trader is angry or distressed.
Only flags clear frustration signals, avoiding false positives on normal
financial keywords like "my money" or "help".
"""

# Strong frustration signals — these clearly indicate anger/distress
STRONG_SIGNALS = [
    "scam", "fraud", "useless", "nonsense", "rubbish", "419", "thief",
    "steal", "ole", "una don thief", "this thing no work", "wahala",
    "banza", "e je mi", "zamba", "where is my money",
    "i want my money back", "you people are", "you dey craze",
    "mad", "foolish", "stupid",
]

# Weak signals — only trigger if combined with negative context
WEAK_SIGNALS = [
    "complaint", "not working", "terrible", "worst", "disappointed",
    "frustrated", "angry", "fed up",
]


def detect_frustration(message: str) -> bool:
    """Return True if the message signals trader frustration."""
    msg = message.lower()

    # Strong signals are always escalated
    if any(signal in msg for signal in STRONG_SIGNALS):
        return True

    # Weak signals need at least 2 present or exclamation marks
    weak_count = sum(1 for signal in WEAK_SIGNALS if signal in msg)
    if weak_count >= 2:
        return True

    # Excessive punctuation (screaming)
    if msg.count("!") >= 3 or msg.count("?") >= 4:
        return True

    return False
