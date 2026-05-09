"""
PII scrubber — strips sensitive data before logging or sending to LLM.

Removes: phone numbers, account numbers, PIN-like sequences, BVN patterns.
"""
import re

_PHONE_RE = re.compile(r"\b(?:\+?234|0)?[789]\d{9}\b")
_ACCOUNT_RE = re.compile(r"\b\d{10}\b")
_PIN_RE = re.compile(r"\b\d{4}\b")
_BVN_RE = re.compile(r"\b\d{11}\b")


def scrub(text: str) -> str:
    """Replace sensitive patterns with redacted placeholders."""
    text = _BVN_RE.sub("[BVN_REDACTED]", text)
    text = _PHONE_RE.sub("[PHONE_REDACTED]", text)
    text = _ACCOUNT_RE.sub("[ACCOUNT_REDACTED]", text)
    text = _PIN_RE.sub("[PIN_REDACTED]", text)
    return text
