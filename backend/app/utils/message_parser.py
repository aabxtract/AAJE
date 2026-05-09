"""
Message parser — classifies inbound WhatsApp messages into intents.
Used by the session router to dispatch active-trader messages.
"""
import re

INTENT_PATTERNS = {
    "log_sale": re.compile(
        r"\b(sold|made|earned|got|collected|received)\b.{0,30}(?:₦|N|NGN)?\d",
        re.IGNORECASE,
    ),
    "log_expense": re.compile(
        r"\b(spent|bought|paid|used|cost)\b.{0,30}(?:₦|N|NGN)?\d",
        re.IGNORECASE,
    ),
    "check_balance": re.compile(
        r"\b(balance|how much|check|vault|savings|kolo)\b",
        re.IGNORECASE,
    ),
    "withdraw": re.compile(
        r"\b(withdraw|take out|move out|send me|transfer to me)\b",
        re.IGNORECASE,
    ),
    "pay_supplier": re.compile(
        r"\b(pay|send to|transfer to)\b.{0,30}(?:₦|N|NGN)?\d",
        re.IGNORECASE,
    ),
    "insight": re.compile(
        r"\b(how am i doing|report|summary|performance|score|business)\b",
        re.IGNORECASE,
    ),
    "help": re.compile(r"\b(help|sos|support|problem|issue)\b", re.IGNORECASE),
}


def classify_intent(text: str) -> str:
    """Return the first matching intent or 'unknown'."""
    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.search(text):
            return intent
    return "unknown"
