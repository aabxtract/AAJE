"""
PII Scrubber - Removes Personal Identifiable Information before sending data to LLM.
"""

import re
import math

def _round_money(value):
    try:
        val = float(value)
        return round(val / 100) * 100
    except (ValueError, TypeError):
        return value

def scrub(raw_context: dict) -> dict:
    """
    Scrubs PII from raw context according to strict rules.
    """
    scrubbed = {}
    remove_keys = {"pin_hash", "mono_account_id", "squad_customer_id", "verified_bank_account", "verified_bank_code"}
    
    for k, v in raw_context.items():
        if k in remove_keys:
            continue
            
        if k == "full_name" and isinstance(v, str):
            scrubbed[k] = v.split()[0] if v else ""
            continue
            
        if "account_number" in k and isinstance(v, str) and len(v) >= 4:
            scrubbed[k] = "***" + v[-4:]
            continue
            
        if isinstance(v, str):
            # Remove 10-digit or 11-digit numbers completely
            if re.fullmatch(r'\d{10,11}', v.strip()):
                continue
                
        # Round money to nearest hundred
        if isinstance(v, (int, float)) and ("amount" in k or "balance" in k or "revenue" in k or "profit" in k):
            scrubbed[k] = _round_money(v)
            continue
            
        if isinstance(v, dict):
            scrubbed[k] = scrub(v)
        elif isinstance(v, list):
            scrubbed[k] = [scrub(item) if isinstance(item, dict) else item for item in v]
        else:
            scrubbed[k] = v
            
    return scrubbed

def scrub_transaction_list(transactions: list[dict]) -> list[dict]:
    scrubbed_list = []
    for tx in transactions:
        s_tx = scrub(tx)
        s_tx.pop("mono_transaction_id", None)
        scrubbed_list.append(s_tx)
    return scrubbed_list
