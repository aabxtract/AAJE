from difflib import SequenceMatcher


def format_naira(amount: float) -> str:
    return f"\u20a6{float(amount):,.2f}"


def names_match(input_name: str, bank_name: str) -> bool:
    a = (input_name or "").upper().strip()
    b = (bank_name or "").upper().strip()
    if a == b:
        return True
    if set(a.split()).issubset(set(b.split())):
        return True
    return SequenceMatcher(None, a, b).ratio() > 0.85


def split_full_name(full_name: str) -> tuple[str, str, str]:
    """Split into (first, middle, last). Squad requires all three non-empty."""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], parts[0], parts[0]
    if len(parts) == 2:
        return parts[0], parts[0], parts[1]
    return parts[0], " ".join(parts[1:-1]), parts[-1]
