import re
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import InventoryMovement, Order, OrderItem, Product, Store
from app.models.marketing import CampaignLink
from app.models.money import VirtualAccount, Wallet
from app.models.user import User
from app.events.handlers import emit_event
from app.payments.squad import create_virtual_account


def _ascii_lower(value: str) -> str:
    return (value or "").encode("ascii", "ignore").decode("ascii").lower()


def generate_store_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "", _ascii_lower(value))
    return slug[:80] or f"store{uuid.uuid4().hex[:8]}"


def normalize_store_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", _ascii_lower(value)).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug[:80] or f"store{uuid.uuid4().hex[:8]}"


def ref_slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:80] or "campaign"


# ── Template selection keywords ──────────────────────────────────────
TEMPLATE_KEYWORDS: dict[str, list[str]] = {
    "fashion": [
        "fashion", "clothes", "clothing", "thrift", "shoes", "sneaker", "bag",
        "jewelry", "wears", "dress", "shirt",
        "boutique", "fabric", "ankara", "leather", "vintage", "style", "wear",
        "apparel", "hat", "cap", "watch",
    ],
    "gadgets": [
        "gadget", "phone", "laptop", "electronics", "tech", "computer",
        "charger", "speaker", "headphone", "earphone", "earbuds", "tablet",
        "console", "gaming", "camera", "drone", "smart", "device", "cable",
        "power bank", "accessory", "accessories", "screen", "protector",
        "repair", "iphone", "samsung", "android",
    ],
    "food": [
        "food", "catering", "drinks", "drink", "restaurant", "kitchen", "cook",
        "bake", "bakery", "snack", "meal", "pepper", "spice", "rice", "jollof",
        "suya", "grill", "juice", "smoothie", "cake", "pastry", "shawarma",
        "burger", "pizza", "coffee", "tea", "wine", "bar", "fish", "chicken",
        "meat", "vegetable", "fruit",
    ],
    "creator": [
        "service", "creator", "freelance", "design", "photography", "photo",
        "video", "music", "art", "craft", "digital", "creative", "writing",
        "tutor", "coaching", "consulting", "makeup", "beauty", "hair", "salon",
        "barber", "tattoo", "event", "dj", "mc", "print", "tailor", "sewing",
    ],
}

# ── Starter product presets per template ─────────────────────────────
_STARTER_PRODUCTS: dict[str, list[dict]] = {
    "fashion": [
        {"name": "Classic T-Shirt", "type": "product", "description": "Premium cotton tee for everyday wear.", "category": "Tops", "price": 8500, "stock_quantity": 20},
        {"name": "Denim Jeans", "type": "product", "description": "Slim-fit denim with stretch comfort.", "category": "Bottoms", "price": 15000, "stock_quantity": 12},
        {"name": "Leather Sneakers", "type": "product", "description": "Handcrafted leather kicks.", "category": "Shoes", "price": 22000, "stock_quantity": 8},
    ],
    "gadgets": [
        {"name": "Fast Charger", "type": "product", "description": "65W USB-C fast charging adapter.", "category": "Accessories", "price": 5500, "stock_quantity": 30},
        {"name": "Wireless Earbuds", "type": "product", "description": "Bluetooth 5.3 earbuds with noise cancellation.", "category": "Audio", "price": 12000, "stock_quantity": 15},
        {"name": "Phone Case", "type": "product", "description": "Shockproof clear case with camera protection.", "category": "Accessories", "price": 3500, "stock_quantity": 50},
    ],
    "food": [
        {"name": "Jollof Rice Platter", "type": "product", "description": "Party-style jollof with chicken and plantain.", "category": "Meals", "price": 3500, "stock_quantity": 25},
        {"name": "Shawarma Wrap", "type": "product", "description": "Beef shawarma with fresh veggies and sauce.", "category": "Snacks", "price": 2500, "stock_quantity": 30},
        {"name": "Fresh Smoothie", "type": "product", "description": "Blended fruits — mango, banana, strawberry.", "category": "Drinks", "price": 2000, "stock_quantity": 20},
    ],
    "creator": [
        {"name": "Basic Package", "type": "service", "description": "Standard service package for new clients.", "category": "Services", "price": 15000, "stock_quantity": 0},
        {"name": "Premium Package", "type": "service", "description": "Full-service premium offering.", "category": "Services", "price": 35000, "stock_quantity": 0},
        {"name": "Consultation", "type": "service", "description": "1-hour consultation session.", "category": "Consultation", "price": 10000, "stock_quantity": 0},
    ],
}

_TEMPLATE_CATEGORIES: dict[str, list[str]] = {
    "fashion": ["Tops", "Bottoms", "Shoes", "Accessories"],
    "gadgets": ["Phones", "Accessories", "Audio", "Computing"],
    "food": ["Meals", "Snacks", "Drinks", "Platters"],
    "creator": ["Services", "Consultation", "Packages"],
}

_TEMPLATE_THEMES: dict[str, str] = {
    "fashion": "warm_coral",
    "gadgets": "dark_blue",
    "food": "fresh_green",
    "creator": "soft_purple",
}

_TEMPLATE_TAGLINES: dict[str, str] = {
    "fashion": "Style that speaks for you.",
    "gadgets": "Smart tech for everyday life.",
    "food": "Fresh flavours delivered to you.",
    "creator": "Quality work, every time.",
}

_LAYOUTS: dict[str, dict] = {
    "catalog_powerhouse": {
        "name": "Catalog Powerhouse",
        "best_for": "stores with many categories and fast-moving stock",
        "hero_style": "split_catalog",
        "product_density": "high",
    },
    "premium_showroom": {
        "name": "Premium Showroom",
        "best_for": "high trust, high-ticket products",
        "hero_style": "large_media",
        "product_density": "medium",
    },
    "deal_stack": {
        "name": "Deal Stack",
        "best_for": "discounts, bundles, and impulse buys",
        "hero_style": "offer_led",
        "product_density": "high",
    },
    "service_booking": {
        "name": "Service Booking",
        "best_for": "creators, repairs, consultations, and appointments",
        "hero_style": "booking_led",
        "product_density": "low",
    },
    "local_market": {
        "name": "Local Market",
        "best_for": "food, provisions, fresh goods, and repeat orders",
        "hero_style": "trust_led",
        "product_density": "medium",
    },
}

_RICH_PRODUCTS: dict[str, dict[str, list[dict]]] = {
    "gadgets": {
        "phones": [
            {"name": "UK Used iPhone 13", "type": "product", "description": "Clean 128GB unit, Face ID working, battery health checked.", "category": "Phones", "price": 430000, "stock_quantity": 4, "low_stock_threshold": 1},
            {"name": "Samsung Galaxy A15", "type": "product", "description": "Dual SIM Android phone with warranty-ready receipt.", "category": "Phones", "price": 185000, "stock_quantity": 6, "low_stock_threshold": 2},
            {"name": "Oraimo Power Bank 20000mAh", "type": "product", "description": "Fast-charging backup power for daily Nigerian use.", "category": "Power", "price": 18500, "stock_quantity": 18, "low_stock_threshold": 4},
            {"name": "AirPods Pro Grade A", "type": "product", "description": "Noise cancelling earbuds with MagSafe-style charging case.", "category": "Audio", "price": 45000, "stock_quantity": 10, "low_stock_threshold": 3},
        ],
        "pcs": [
            {"name": "HP EliteBook 840 G5", "type": "product", "description": "Core i5, 8GB RAM, 256GB SSD, tested for office and school work.", "category": "Laptops", "price": 245000, "stock_quantity": 5, "low_stock_threshold": 1},
            {"name": "Dell Latitude 7490", "type": "product", "description": "Business laptop with strong battery and clean keyboard.", "category": "Laptops", "price": 265000, "stock_quantity": 4, "low_stock_threshold": 1},
            {"name": "Wireless Mouse + Keyboard Combo", "type": "product", "description": "Affordable desk setup bundle for students and remote workers.", "category": "Accessories", "price": 18000, "stock_quantity": 12, "low_stock_threshold": 3},
            {"name": "Laptop Charger Replacement", "type": "product", "description": "Reliable replacement chargers for HP, Dell, and Lenovo laptops.", "category": "Power", "price": 15000, "stock_quantity": 15, "low_stock_threshold": 4},
        ],
        "repairs": [
            {"name": "Phone Screen Replacement", "type": "service", "description": "Screen replacement service for popular iPhone and Android models.", "category": "Repairs", "price": 35000, "stock_quantity": 20, "low_stock_threshold": 3},
            {"name": "Laptop Diagnosis", "type": "service", "description": "Hardware and software check with clear repair quote.", "category": "Repairs", "price": 10000, "stock_quantity": 25, "low_stock_threshold": 5},
            {"name": "Data Recovery Service", "type": "service", "description": "Recover files from faulty drives, phones, and memory cards.", "category": "Services", "price": 25000, "stock_quantity": 10, "low_stock_threshold": 2},
            {"name": "Tempered Glass Install", "type": "service", "description": "Quick screen protection installation for phones and tablets.", "category": "Accessories", "price": 3500, "stock_quantity": 40, "low_stock_threshold": 8},
        ],
        "general": [
            {"name": "Fast USB-C Charger", "type": "product", "description": "Compact 30W fast charger for phones and accessories.", "category": "Accessories", "price": 12000, "stock_quantity": 20, "low_stock_threshold": 5},
            {"name": "Bluetooth Speaker", "type": "product", "description": "Portable loud speaker for home, shop, and hangouts.", "category": "Audio", "price": 28000, "stock_quantity": 9, "low_stock_threshold": 2},
            {"name": "Type-C Cable Pack", "type": "product", "description": "Durable fast-charge cable bundle for Android and modern devices.", "category": "Cables", "price": 6500, "stock_quantity": 35, "low_stock_threshold": 8},
            {"name": "MagSafe Phone Case", "type": "product", "description": "Slim protective case with magnetic charging support.", "category": "Accessories", "price": 9500, "stock_quantity": 16, "low_stock_threshold": 4},
        ],
    },
}


def _detect_template(text: str) -> str:
    """Match business description keywords to a template name."""
    lower = text.lower()
    scores: dict[str, int] = {t: 0 for t in TEMPLATE_KEYWORDS}
    for template, keywords in TEMPLATE_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[template] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "fashion"


def _detect_focus(template: str, text: str) -> str:
    lower = text.lower()
    if template == "gadgets":
        if any(word in lower for word in ["laptop", "pc", "computer", "desktop", "macbook"]):
            return "pcs"
        if any(word in lower for word in ["repair", "screen", "fix", "technician", "service"]):
            return "repairs"
        if any(word in lower for word in ["phone", "iphone", "samsung", "android"]):
            return "phones"
        return "general"
    return "general"


def _detect_layout(template: str, text: str, focus: str) -> str:
    lower = text.lower()
    if template == "creator" or focus == "repairs" or any(word in lower for word in ["service", "booking", "appointment", "repair"]):
        return "service_booking"
    if any(word in lower for word in ["premium", "luxury", "high ticket", "iphone", "macbook", "imported", "uk used"]):
        return "premium_showroom"
    if any(word in lower for word in ["deal", "discount", "bundle", "promo", "cheap", "affordable"]):
        return "deal_stack"
    if template == "food":
        return "local_market"
    return "catalog_powerhouse"


def _store_name_from_description(description: str, template: str) -> str:
    match = re.search(r"store name:\s*([^\n]+)", description, re.IGNORECASE)
    if match:
        return match.group(1).strip()[:80]
    words = [w.capitalize() for w in re.findall(r"[A-Za-z]+", description) if len(w) > 2]
    if words:
        return " ".join(words[:3])
    return {
        "gadgets": "AAJE Gadget Hub",
        "fashion": "AAJE Fashion House",
        "food": "AAJE Kitchen Market",
        "creator": "AAJE Creator Studio",
    }.get(template, "AAJE Store")


def _categories_for(template: str, focus: str) -> list[str]:
    if template == "gadgets":
        return {
            "phones": ["Phones", "Audio", "Power", "Accessories"],
            "pcs": ["Laptops", "Accessories", "Power", "Repairs"],
            "repairs": ["Repairs", "Services", "Accessories", "Diagnostics"],
            "general": ["Accessories", "Audio", "Power", "Cables"],
        }[focus]
    return _TEMPLATE_CATEGORIES[template]


def _products_for(template: str, focus: str) -> list[dict]:
    if template in _RICH_PRODUCTS and focus in _RICH_PRODUCTS[template]:
        return _RICH_PRODUCTS[template][focus]
    return _STARTER_PRODUCTS[template]


def _questions_for(template: str, focus: str) -> list[str]:
    if template == "gadgets":
        return [
            "Do you sell mostly phones, laptops/PCs, accessories, or repair services?",
            "Do you want customers to see warranty, condition, or delivery details on each product?",
            "Upload or paste a display photo so the storefront hero can look like your real shop.",
        ]
    return [
        "What product line should customers see first?",
        "Do you have brand photos or a logo for the storefront hero?",
        "Should the store feel premium, affordable, local, or playful?",
    ]


async def generate_store_blueprint(description: str) -> dict:
    """AI config generator: returns a StoreConfig JSON from a business prompt."""
    template = _detect_template(description)
    focus = _detect_focus(template, description)
    layout_key = _detect_layout(template, description, focus)
    layout = _LAYOUTS[layout_key]
    store_name = _store_name_from_description(description, template)
    categories = _categories_for(template, focus)
    products = _products_for(template, focus)

    return {
        "template": template,
        "layout": layout_key,
        "layout_config": layout,
        "business_focus": focus,
        "theme": _TEMPLATE_THEMES[template],
        "store_name": store_name,
        "tagline": _TEMPLATE_TAGLINES[template],
        "description": description,
        "categories": categories,
        "products": products,
        "sections": [
            {"type": "hero", "title": store_name, "style": layout["hero_style"]},
            {"type": "category_rail", "title": "Shop by need", "items": categories},
            {"type": "featured_products", "title": "Recommended for your customers"},
            {"type": "trust_bar", "items": ["WhatsApp ordering", "Squad payments", "Inventory tracked"]},
        ],
        "ai_suggestions": _questions_for(template, focus),
    }


async def create_store(db: AsyncSession, user: User, payload: dict) -> Store:
    store_name = payload["store_name"]
    base_slug = normalize_store_slug(payload["slug"]) if payload.get("slug") else generate_store_slug(store_name)
    slug = base_slug
    suffix = 2
    while (await db.execute(select(Store).where((Store.slug == slug) | (Store.store_slug == slug)))).scalar_one_or_none():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    # Build config_json from payload
    config_json = payload.get("config_json") or {
        "template": payload.get("template", "fashion"),
        "theme": payload.get("theme") if isinstance(payload.get("theme"), str) else "default",
        "store_name": store_name,
        "tagline": payload.get("tagline", ""),
        "description": payload.get("description", ""),
        "categories": payload.get("categories", []),
        "products": payload.get("starter_products", []),
    }

    store = Store(
        user_id=user.id,
        store_name=store_name,
        slug=slug,
        store_slug=slug,
        description=payload.get("description"),
        store_description=payload.get("description"),
        tagline=payload.get("tagline"),
        theme_json=payload.get("theme_json") or {},
        theme=config_json.get("theme", "default"),
        template=config_json.get("template", "fashion"),
        config_json=config_json,
        contact_whatsapp=user.whatsapp_no,
        whatsapp_number=user.whatsapp_no or user.phone,
        has_squad_account=bool(payload.get("has_squad_account", False)),
    )
    db.add(store)
    user.onboarding_complete = True
    await db.flush()

    for product in payload.get("starter_products") or []:
        await create_product(db, store, product, emit=False)

    await emit_event(db, {
        "event_type": "store_created",
        "source": "storefront",
        "user_id": str(user.id),
        "store_id": str(store.id),
        "metadata": {"store_name": store.store_name, "slug": store.slug, "template": store.template},
    })
    return store


async def create_storefront_from_description(db: AsyncSession, user: User, description: str, create_squad_account: bool = True) -> Store:
    user.business_description = description
    blueprint = await generate_store_blueprint(description)
    store = await create_store(db, user, {
        "store_name": blueprint["store_name"],
        "description": blueprint.get("description", description),
        "tagline": blueprint.get("tagline"),
        "template": blueprint.get("template", "fashion"),
        "theme": blueprint.get("theme", "default"),
        "categories": blueprint.get("categories", []),
        "starter_products": blueprint.get("products", []),
        "config_json": blueprint,
        "has_squad_account": create_squad_account,
    })
    await ensure_wallet(db, user.id)
    if create_squad_account:
        await ensure_store_virtual_account(db, user, store)
    return store


async def ensure_wallet(db: AsyncSession, user_id) -> Wallet:
    wallet = (await db.execute(select(Wallet).where(Wallet.user_id == user_id))).scalar_one_or_none()
    if wallet:
        return wallet
    wallet = Wallet(user_id=user_id)
    db.add(wallet)
    await db.flush()
    return wallet


async def ensure_store_virtual_account(db: AsyncSession, user: User, store: Store) -> VirtualAccount:
    existing = (await db.execute(select(VirtualAccount).where(VirtualAccount.user_id == user.id, VirtualAccount.is_primary.is_(True)))).scalar_one_or_none()
    if existing:
        store.squad_virtual_account_id = existing.squad_account_id
        store.squad_virtual_account_number = existing.account_number
        store.has_squad_account = True
        return existing

    names = (user.full_name or store.store_name or "AAJE Trader").split()
    first_name = names[0]
    last_name = names[-1] if len(names) > 1 else "Trader"
    customer_id = user.squad_customer_id or f"AAJE-{uuid.uuid4().hex[:12]}"
    result = await create_virtual_account(
        customer_id=customer_id,
        first_name=first_name,
        middle_name="",
        last_name=last_name,
        phone=user.whatsapp_no or user.phone or "08000000000",
        beneficiary_account=user.verified_bank_account or "0000000000",
    )
    account_number = (
        result.get("account_number")
        or result.get("virtual_account_number")
        or result.get("account", {}).get("account_number")
    )
    account_id = result.get("account_id") or result.get("id") or result.get("virtual_account_id")
    virtual_account = VirtualAccount(
        user_id=user.id,
        account_name=store.store_name,
        account_number=account_number,
        squad_account_id=account_id,
        bank_name=result.get("bank_name") or "GTBank",
        is_primary=True,
    )
    db.add(virtual_account)
    user.squad_customer_id = result.get("customer_identifier") or customer_id
    store.squad_customer_identifier = user.squad_customer_id
    store.squad_virtual_account_id = account_id
    store.squad_virtual_account_number = account_number
    store.has_squad_account = bool(account_number)
    await db.flush()
    return virtual_account


async def create_product(db: AsyncSession, store: Store, payload: dict, emit: bool = True) -> Product:
    product = Product(
        store_id=store.id,
        user_id=store.user_id,
        name=payload["name"],
        description=payload.get("description"),
        type=payload.get("type", "product"),
        category=payload.get("category"),
        price=Decimal(str(payload.get("price") or 0)),
        image_url=payload.get("image_url"),
        stock_quantity=int(payload.get("stock_quantity") or 0),
        low_stock_threshold=int(payload.get("low_stock_threshold") or 5),
        is_active=payload.get("is_active", True),
        is_available=payload.get("is_available", payload.get("is_active", True)),
        source=payload.get("source", "web"),
    )
    db.add(product)
    await db.flush()
    db.add(InventoryMovement(
        store_id=store.id,
        product_id=product.id,
        movement_type="in",
        quantity=product.stock_quantity or 0,
        reason="product_created",
    ))
    if emit:
        await emit_event(db, {
            "event_type": "product_created",
            "source": "storefront",
            "user_id": str(store.user_id),
            "store_id": str(store.id),
            "product_id": str(product.id),
            "metadata": {"product_name": product.name, "stock_quantity": product.stock_quantity},
        })
    return product


async def create_order(db: AsyncSession, store: Store, payload: dict) -> Order:
    items_payload = payload.get("items") or []
    if not items_payload:
        raise ValueError("Order requires at least one item")

    if len(items_payload) > 4:
        raise ValueError("Cart may contain at most 4 products")

    if not payload.get("customer_phone") or not payload.get("customer_name"):
        raise ValueError("Customer name and phone are required")

    total = Decimal("0")
    resolved_items = []
    for item in items_payload:
        product = await db.get(Product, item["product_id"])
        if not product or product.store_id != store.id:
            raise ValueError("Invalid product for this store")
        quantity = int(item.get("quantity") or 1)
        if product.type != "service" and (product.stock_quantity or 0) < quantity:
            raise ValueError(f"{product.name} is out of stock")
        line_total = Decimal(product.price) * quantity
        total += line_total
        resolved_items.append((product, quantity, line_total))

    campaign_ref = payload.get("campaign_ref")
    if campaign_ref:
        campaign = (await db.execute(
            select(CampaignLink).where(
                CampaignLink.store_id == store.id,
                CampaignLink.ref_slug == ref_slugify(campaign_ref),
            )
        )).scalar_one_or_none()
        if not campaign:
            raise ValueError("Invalid campaign ref for this store")
        campaign_ref = campaign.ref_slug

    reference = payload.get("payment_reference") or f"AAJE-{uuid.uuid4().hex[:16].upper()}"
    order = Order(
        store_id=store.id,
        user_id=store.user_id,
        customer_name=payload.get("customer_name"),
        customer_phone=payload.get("customer_phone"),
        customer_whatsapp=payload.get("customer_whatsapp") or payload.get("customer_phone"),
        total_amount=total,
        squad_payment_reference=reference,
        squad_transaction_ref=reference,
        status="pending",
        notes=payload.get("notes"),
        campaign_ref=campaign_ref,
        idempotency_key=payload.get("idempotency_key") or reference,
    )
    db.add(order)
    await db.flush()
    for product, quantity, line_total in resolved_items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            unit_price=product.price,
            total_price=line_total,
            subtotal=line_total,
        ))

    await emit_event(db, {
        "event_type": "order_created",
        "source": "storefront",
        "user_id": str(store.user_id),
        "store_id": str(store.id),
        "order_id": str(order.id),
        "amount": float(total),
        "reference": reference,
        "campaign_ref": campaign_ref,
    })
    return order
