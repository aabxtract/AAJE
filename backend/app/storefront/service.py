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


async def generate_store_blueprint(description: str) -> dict:
    words = [w.capitalize() for w in re.findall(r"[A-Za-z]+", description)[:3]]
    base = " ".join(words) or "AAJE Store"
    return {
        "store_name": f"{base} Market",
        "tagline": "Simple, trusted, and ready for customers.",
        "description": description,
        "categories": ["Popular", "New Arrivals", "Services"],
        "theme": "clean_minimal",
        "starter_products": [
            {"name": "Starter Item", "type": "product", "description": "Edit this item after setup.", "category": "Popular", "price": 5000, "stock_quantity": 10},
        ],
    }


async def create_store(db: AsyncSession, user: User, payload: dict) -> Store:
    store_name = payload["store_name"]
    base_slug = normalize_store_slug(payload["slug"]) if payload.get("slug") else generate_store_slug(store_name)
    slug = base_slug
    suffix = 2
    while (await db.execute(select(Store).where((Store.slug == slug) | (Store.store_slug == slug)))).scalar_one_or_none():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    store = Store(
        user_id=user.id,
        store_name=store_name,
        slug=slug,
        store_slug=slug,
        description=payload.get("description"),
        store_description=payload.get("description"),
        tagline=payload.get("tagline"),
        theme_json=payload.get("theme_json") or payload.get("theme") or {},
        theme=(payload.get("theme") or {}).get("name") if isinstance(payload.get("theme"), dict) else payload.get("theme", "default"),
        contact_whatsapp=user.whatsapp_no,
        whatsapp_number=user.whatsapp_no or user.phone,
        has_squad_account=bool(payload.get("has_squad_account", False)),
    )
    db.add(store)
    await db.flush()

    for product in payload.get("starter_products") or []:
        await create_product(db, store, product, emit=False)

    await emit_event(db, {
        "event_type": "store_created",
        "source": "storefront",
        "user_id": str(user.id),
        "store_id": str(store.id),
        "metadata": {"store_name": store.store_name, "slug": store.slug},
    })
    return store


async def create_storefront_from_description(db: AsyncSession, user: User, description: str, create_squad_account: bool = True) -> Store:
    user.business_description = description
    blueprint = await generate_store_blueprint(description)
    store = await create_store(db, user, {
        "store_name": blueprint["store_name"],
        "description": blueprint["store_description"] if "store_description" in blueprint else blueprint["description"],
        "tagline": blueprint.get("tagline"),
        "theme": blueprint.get("theme") or "clean_minimal",
        "starter_products": blueprint.get("products") or blueprint.get("starter_products") or [],
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

    # Enforce cart max size
    if len(items_payload) > 4:
        raise ValueError("Cart may contain at most 4 products")

    # Require customer contact info for guest checkout
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
