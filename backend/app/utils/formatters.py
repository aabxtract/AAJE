from datetime import datetime, timezone
from difflib import SequenceMatcher

from app.redis import increment_order_counter


def format_naira(amount: float) -> str:
    return f"\u20a6{float(amount):,.2f}"


def build_store_url(slug: str) -> str:
    """Build the public storefront URL using subdomain routing.

    - Prod: ``https://{slug}.aaje.store``
    - Dev:  ``http://{slug}.localtest.me:5174`` (or :4173 for preview)

    Reads ``settings.frontend_url``; the FIRST entry (comma-separated list)
    is used as the apex source-of-truth. ``localhost`` is rewritten to
    ``localtest.me`` so any subdomain resolves to 127.0.0.1 without
    /etc/hosts edits.
    """
    from urllib.parse import urlparse

    from app.config import settings

    raw = (settings.frontend_url or "https://aaje.store").split(",")[0].strip()
    if not raw:
        raw = "https://aaje.store"
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    scheme = parsed.scheme or "https"
    host = (parsed.hostname or "aaje.store").lower()
    port = parsed.port

    # localhost / 127.0.0.1 \u2192 localtest.me so the subdomain resolves
    if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
        host = "localtest.me"

    netloc = f"{slug}.{host}"
    if port:
        netloc += f":{port}"
    return f"{scheme}://{netloc}"


async def generate_order_ref() -> str:
    """Produce AAJE-YYYY-NNNN. NNNN is a per-year counter held in Redis.

    After 9999 orders in a year, format widens to AAJE-YYYY-NNNNN (no
    collision risk \u2014 order_ref column is VARCHAR(20)).
    """
    year = datetime.now(timezone.utc).year
    count = await increment_order_counter(year)
    width = 4 if count < 10000 else 5
    return f"AAJE-{year}-{count:0{width}d}"


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
