import re
import uuid
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Store, Product
from app.config import settings
from app.services.whatsapp_client import send_cta_button


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:200]


async def generate_store_payload(input_data: Dict[str, Any]) -> Dict[str, Any]:
    business = (input_data.get("business_type") or "My Business").strip()
    style = input_data.get("preferred_style") or "clean"
    target = input_data.get("target_audience") or "local customers"
    products = input_data.get("products") or []

    store_name = input_data.get("store_name") or f"{business.title()} Shop"
    tagline = input_data.get("tagline") or f"{business.title()} for {target}"
    description = input_data.get("description") or f"A {style} store selling {business}."

    if products:
        categories = list({(p.get("category") or "General") for p in products})
    else:
        categories = ["General"]

    primary_color = {
        "clean": "#1f8fff",
        "bold": "#ff5722",
        "local": "#009688",
        "premium": "#52307c",
        "playful": "#ffb400",
    }.get(style, "#1f8fff")

    starter_products: List[Dict[str, Any]] = []
    for p in products[:6]:
        starter_products.append(
            {
                "name": p.get("name") or "Sample Item",
                "category": p.get("category") or categories[0],
                "description": p.get("description") or "",
                "suggested_price": p.get("price"),
                "stock": p.get("stock") or 0,
            }
        )

    if not starter_products:
        starter_products = [
            {
                "name": "Sample Item",
                "category": categories[0],
                "description": "Starter product",
                "suggested_price": None,
                "stock": 0,
            }
        ]

    payload = {
        "store_name": store_name,
        "tagline": tagline,
        "description": description,
        "categories": categories,
        "theme": {"style": style, "primary_color": primary_color, "layout": "simple_grid"},
        "starter_products": starter_products,
    }

    return payload


async def create_store(
    session: AsyncSession, user_id: uuid.UUID, payload: Dict[str, Any], create_products: bool = True
) -> Store:
    slug = _slugify(payload.get("store_name") or "store")
    store = Store(
        user_id=user_id,
        store_name=payload.get("store_name"),
        slug=slug,
        description=payload.get("description"),
        theme_json=payload.get("theme"),
        contact_whatsapp=payload.get("contact_whatsapp"),
    )
    session.add(store)
    await session.flush()

    if create_products:
        for p in payload.get("starter_products", []):
            prod = Product(
                store_id=store.id,
                name=p.get("name"),
                description=p.get("description"),
                category=p.get("category"),
                price=p.get("suggested_price") or 0,
                stock_quantity=p.get("stock") or 0,
            )
            session.add(prod)
        await session.flush()

    # Notify owner via WhatsApp with store link if contact provided
    try:
        if store.contact_whatsapp and settings.app_public_url:
            store_url = f"{settings.app_public_url.rstrip('/')}/store/{store.slug}"
            await send_cta_button(
                to=store.contact_whatsapp,
                body=f"Your store '{store.store_name}' is ready!",
                button_label="View Store",
                url=store_url,
            )
    except Exception:
        pass

    return store
