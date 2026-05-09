"""
Frustration detector — identifies when a trader is struggling.

Triggers escalation or simplified help message when detected.
"""
import re

_FRUSTRATION_PATTERNS = re.compile(
    r"\b(confused|don't understand|what is this|stop|cancel|quit|abi|wetin|"
    r"i don't get|this is hard|help me|i'm lost|no understand)\b",
    re.IGNORECASE,
)


def is_frustrated(text: str) -> bool:
    return bool(_FRUSTRATION_PATTERNS.search(text))
