"""PII scrubbing for LLM safety.

Per CLAUDE.md §13 and §18 rule 10, this runs BEFORE every LLM call.
The LLM never sees raw account numbers, hashed credentials, or precise
monetary amounts that could fingerprint a specific user.

Rules:
- Account numbers (10-11 consecutive digits) → ``***LAST4``
- ``full_name`` → first name only
- Removed entirely: password_hash, pin_hash, bank_code, account_number,
  squad_customer_id, mono_account_id, verified_bank_*
- Numeric monetary amounts → rounded to nearest ₦100
"""
import copy
import re


REMOVE_KEYS = {
    "password_hash",
    "pin_hash",
    "account_number",
    "bank_code",
    "verified_bank_account",
    "verified_bank_code",
    "verified_bank_name",
    "squad_customer_id",
    "mono_account_id",
}


def _clean(value):
    if isinstance(value, dict):
        return scrub(value)
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, str):
        return re.sub(r"\b\d{10,11}\b", lambda m: f"***{m.group(0)[-4:]}", value)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        # Round to nearest ₦100 — defeats unique-amount fingerprinting
        return round(float(value) / 100) * 100
    return value


def scrub(data: dict) -> dict:
    """Return a scrubbed copy of ``data``. Never mutates the input."""
    cleaned: dict = {}
    for key, value in copy.deepcopy(data).items():
        if key in REMOVE_KEYS:
            continue
        if key == "full_name" and isinstance(value, str):
            cleaned[key] = value.split()[0] if value else ""
            continue
        cleaned[key] = _clean(value)
    return cleaned
