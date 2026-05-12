import copy
import re


REMOVE_KEYS = {
    "pin_hash",
    "squad_customer_id",
    "verified_bank_account",
    "verified_bank_code",
    "mono_account_id",
}


def _clean(value):
    if isinstance(value, dict):
        return scrub(value)
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, str):
        return re.sub(r"\b\d{10,11}\b", lambda m: f"***{m.group(0)[-4:]}", value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return round(float(value) / 100) * 100
    return value


def scrub(data: dict) -> dict:
    cleaned = {}
    for key, value in copy.deepcopy(data).items():
        if key in REMOVE_KEYS:
            continue
        if key == "full_name" and isinstance(value, str):
            cleaned[key] = value.split()[0] if value else ""
            continue
        cleaned[key] = _clean(value)
    return cleaned
