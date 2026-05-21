from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.llm_client import get_llm
from app.models.store import Store

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a store-generation assistant for AAJE, a platform for Nigerian traders.

Given a trader's plain-text description of their business, extract a structured store config.

Return ONLY valid JSON in this EXACT shape:
{
  "store_name": "short, friendly name (2-5 words)",
  "store_description": "1-2 sentence description for customers",
  "suggested_slug": "url-safe-slug-here",
  "theme_config": {
    "primary_color": "#hex",
    "accent_color": "#hex",
    "font_style": "modern",
    "layout": "grid",
    "hero_text": "short tagline"
  },
  "products": [
    {
      "name": "Product Name",
      "suggested_price": 2500.0,
      "category": "category name",
      "short_description": "1 sentence description"
    }
  ]
}

Rules:
- Extract every product the trader mentions with a price.
- Prices are in Nigerian Naira. Parse "₦", "N", "NGN", "k" (thousand), or bare numbers.
- font_style must be one of: modern, traditional, playful, minimal.
- layout must be one of: grid, featured, minimal.
- Slug must be lowercase, hyphens only, no special chars.
- Use vibrant Nigerian-appropriate colors (deep greens, oranges, blues, golds).
- If no products are mentioned, return an empty products array.
- Output ONLY the JSON object. No markdown fences, no commentary."""


_SAFE_DEFAULTS: dict[str, Any] = {
    "store_name": "My Store",
    "store_description": "A small business on AAJE.",
    "suggested_slug": "my-store",
    "theme_config": {
        "primary_color": "#0F766E",
        "accent_color": "#F59E0B",
        "font_style": "modern",
        "layout": "grid",
        "hero_text": "Welcome to my store",
    },
    "products": [],
}


async def generate_store_from_description(description: str) -> dict[str, Any]:
    """Extract structured store config from a free-text business description.

    Calls the LLM; retries once with a stricter prompt on parse failure; falls
    back to safe defaults if both attempts fail. Never raises — caller can
    trust the return value is always a usable dict matching _SAFE_DEFAULTS shape.
    """
    try:
        result = await _call_llm(description, strict=False)
        if result:
            return _merge_with_defaults(result)
    except Exception:
        logger.exception("Store generation first attempt failed")

    try:
        result = await _call_llm(description, strict=True)
        if result:
            return _merge_with_defaults(result)
    except Exception:
        logger.exception("Store generation retry failed")

    logger.warning("Store generator using safe defaults — trader will see empty store")
    return _SAFE_DEFAULTS


async def _call_llm(description: str, strict: bool) -> dict | None:
    llm = get_llm()
    system = _SYSTEM_PROMPT
    if strict:
        system += (
            "\n\nIMPORTANT: Your previous response was not valid JSON. "
            "Return ONLY a JSON object. No prose, no markdown fences."
        )

    response = await llm.complete(
        system=system,
        messages=[{"role": "user", "content": description}],
        temperature=0.7,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )
    content = (response.get("content") or "").strip()
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Store generator returned invalid JSON: %s", content[:300])
        return None


def _merge_with_defaults(extracted: dict) -> dict:
    """Ensure all keys exist; fill missing with defaults; coerce types."""
    result: dict[str, Any] = {
        "store_name": str(extracted.get("store_name") or _SAFE_DEFAULTS["store_name"])[:100],
        "store_description": (
            str(extracted.get("store_description") or _SAFE_DEFAULTS["store_description"])[:500]
        ),
        "suggested_slug": str(extracted.get("suggested_slug") or "") or None,
    }

    theme_default = _SAFE_DEFAULTS["theme_config"]
    theme = dict(theme_default)
    extracted_theme = extracted.get("theme_config") or {}
    if isinstance(extracted_theme, dict):
        for key, default_value in theme_default.items():
            value = extracted_theme.get(key)
            if value is not None:
                theme[key] = value
    result["theme_config"] = theme

    products_raw = extracted.get("products")
    result["products"] = products_raw if isinstance(products_raw, list) else []
    return result


async def generate_slug(seed: str, db: AsyncSession) -> str:
    """Convert ``seed`` to a URL-safe unique slug.

    Appends ``-2``, ``-3``, ... on collision. After 100 collisions, appends a
    short random suffix instead.
    """
    base = _slugify(seed) or "store"
    candidate = base
    suffix = 1
    while True:
        existing = await db.execute(select(Store).where(Store.store_slug == candidate))
        if existing.scalar_one_or_none() is None:
            return candidate
        suffix += 1
        candidate = f"{base}-{suffix}"
        if suffix > 100:
            return f"{base}-{uuid.uuid4().hex[:6]}"


def _slugify(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = text.strip("-")
    return text[:80]
