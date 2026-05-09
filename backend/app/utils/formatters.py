from difflib import SequenceMatcher

def names_match(trader_input: str, bank_name: str) -> bool:
    a = trader_input.upper().strip()
    b = bank_name.upper().strip()

    # Exact match
    if a == b:
        return True

    # All words in input exist in bank name
    a_words = set(a.split())
    b_words = set(b.split())
    if a_words.issubset(b_words):
        return True

    # Fuzzy match — handles typos
    ratio = SequenceMatcher(None, a, b).ratio()
    if ratio >= 0.85:
        return True

    return False

def format_naira(amount: float) -> str:
    return f"₦{amount:,.2f}"

def split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])
