from datetime import datetime, timezone
from decimal import Decimal
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import Order, Product, Store
from app.models.intelligence import BizPrintSnapshot
from app.events.handlers import emit_event
from app.services.flows import create_flow_session
from app.storefront.service import create_product


async def get_store_by_user(db: AsyncSession, user_id: str):
    return (await db.execute(select(Store).where(Store.user_id == user_id))).scalar_one_or_none()


async def get_store_orders(db: AsyncSession, store_id: str):
    return (await db.execute(select(Order).where(Order.store_id == store_id).order_by(Order.created_at.desc()))).scalars().all()


def _order_payload(order: Order) -> dict:
    return {
        "id": str(order.id),
        "short_id": str(order.id)[:8],
        "customer_name": order.customer_name,
        "total_amount": float(order.total_amount or 0),
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "created_at": str(order.created_at),
    }


async def get_recent_orders(db: AsyncSession, store_id: str):
    orders = await get_store_orders(db, store_id)
    return [_order_payload(order) for order in orders[:5]]


async def get_pending_orders(db: AsyncSession, store_id: str):
    orders = await get_store_orders(db, store_id)
    pending = [order for order in orders if order.order_status not in {"fulfilled", "delivered", "cancelled"}]
    return [_order_payload(order) for order in pending[:5]]


async def get_today_sales(db: AsyncSession, store_id: str):
    today = datetime.now(timezone.utc).date()
    orders = await get_store_orders(db, store_id)
    paid = [order for order in orders if order.payment_status == "paid" and order.paid_at and order.paid_at.date() == today]
    return {"count": len(paid), "amount": float(sum(order.total_amount or 0 for order in paid))}


async def get_low_stock_products(db: AsyncSession, store_id: str):
    result = await db.execute(select(Product).where(Product.store_id == store_id))
    products = [p for p in result.scalars().all() if (p.stock_quantity or 0) <= (p.low_stock_threshold or 0)]
    return [
        {
            "id": str(product.id),
            "name": product.name,
            "stock_quantity": product.stock_quantity or 0,
            "low_stock_threshold": product.low_stock_threshold or 0,
        }
        for product in products
    ]


async def get_top_products(db: AsyncSession, store_id: str):
    rows = await db.execute(
        select(Product.name, func.coalesce(func.sum(Order.total_amount), 0).label("sales"))
        .select_from(Product)
        .join(Order, Order.store_id == Product.store_id, isouter=True)
        .where(Product.store_id == store_id)
        .group_by(Product.name)
        .limit(5)
    )
    return [{"name": name, "sales": float(sales or 0)} for name, sales in rows.all()]


async def get_store_link(db: AsyncSession, store_id: str):
    store = await db.get(Store, store_id)
    return f"/{store.slug}" if store else None


async def create_product_from_chat(db: AsyncSession, user_id: str, product_data: dict):
    store = await get_store_by_user(db, user_id)
    if not store:
        return None
    return await create_product(db, store, product_data)


async def update_inventory(db: AsyncSession, product_id: str, quantity: int):
    product = await db.get(Product, product_id)
    if not product:
        return None
    product.stock_quantity = max((product.stock_quantity or 0) + int(quantity), 0)
    await emit_event(db, {
        "event_type": "stock_added" if quantity >= 0 else "stock_removed",
        "source": "whatsapp",
        "user_id": str((await db.get(Store, product.store_id)).user_id),
        "store_id": str(product.store_id),
        "product_id": str(product.id),
        "quantity": quantity,
    })
    return product


async def update_inventory_from_chat(db: AsyncSession, store_id: str, message: str):
    product = await _product_from_message(db, store_id, message)
    if not product:
        return {"error": "I could not match that product. Send: update stock Product Name 20."}

    number = _first_int(message)
    if number is None:
        return {"error": "Send the stock quantity as a number. Example: update stock Ankara Bag 12."}

    text = message.lower()
    old_quantity = product.stock_quantity or 0
    if any(term in text for term in {"add", "increase", "restock"}):
        product.stock_quantity = old_quantity + number
        movement_type = "in"
        movement_quantity = number
    elif any(term in text for term in {"remove", "reduce", "subtract"}):
        product.stock_quantity = max(old_quantity - number, 0)
        movement_type = "out"
        movement_quantity = number
    else:
        product.stock_quantity = max(number, 0)
        movement_type = "adjustment"
        movement_quantity = product.stock_quantity - old_quantity

    await emit_event(db, {
        "event_type": "stock_added" if movement_quantity >= 0 else "stock_removed",
        "source": "whatsapp",
        "user_id": str((await db.get(Store, product.store_id)).user_id),
        "store_id": str(product.store_id),
        "product_id": str(product.id),
        "quantity": movement_quantity,
        "metadata": {"product_name": product.name, "stock_quantity": product.stock_quantity},
    }, process_now=False)
    return {"product_name": product.name, "stock_quantity": product.stock_quantity, "movement_type": movement_type}


async def create_product_from_chat_message(db: AsyncSession, user_id: str, message: str):
    store = await get_store_by_user(db, user_id)
    if not store:
        return {"error": "You do not have a connected store yet."}

    price = _price_from_message(message)
    if price is None:
        return {"error": "Send product details with a price. Example: add product Ankara Bag price 15000 stock 8."}

    stock = _stock_from_message(message) or 0
    name = _product_name_from_create_message(message)
    if not name:
        return {"error": "Send the product name. Example: add product Ankara Bag price 15000 stock 8."}

    product = await create_product(db, store, {
        "name": name,
        "price": price,
        "stock_quantity": stock,
        "source": "whatsapp",
    })
    return {"id": str(product.id), "name": product.name, "price": float(product.price or 0), "stock_quantity": product.stock_quantity or 0}


async def mark_order_fulfilled_from_chat(db: AsyncSession, store_id: str, message: str):
    order = await _order_from_message(db, store_id, message)
    if not order:
        return {"error": "I could not match that order. Send: mark order 12345678 fulfilled."}
    order.order_status = "fulfilled"
    order.status = "fulfilled"
    await emit_event(db, {
        "event_type": "order_fulfilled",
        "source": "whatsapp",
        "user_id": str(order.user_id),
        "store_id": str(order.store_id),
        "order_id": str(order.id),
    }, process_now=False)
    return {"id": str(order.id), "short_id": str(order.id)[:8]}


async def generate_store_insight(db: AsyncSession, store_id: str):
    sales = await get_today_sales(db, store_id)
    low_stock = await get_low_stock_products(db, store_id)
    return f"Today you have {sales['count']} paid order(s) worth NGN {sales['amount']:,.2f}. {len(low_stock)} product(s) are low in stock."


async def _product_from_message(db: AsyncSession, store_id: str, message: str) -> Product | None:
    products = (await db.execute(select(Product).where(Product.store_id == store_id))).scalars().all()
    text = message.lower()
    matches = [product for product in products if product.name.lower() in text]
    if matches:
        return max(matches, key=lambda product: len(product.name))
    cleaned = re.sub(r"\b(add|update|set|stock|inventory|to|by|increase|reduce|remove|restock)\b", " ", text)
    cleaned = re.sub(r"\d+", " ", cleaned)
    words = {word for word in cleaned.split() if len(word) > 2}
    for product in products:
        if any(word in product.name.lower() for word in words):
            return product
    return None


async def _order_from_message(db: AsyncSession, store_id: str, message: str) -> Order | None:
    token_match = re.search(r"\b([0-9a-f]{8,})\b", message.lower())
    orders = await get_store_orders(db, store_id)
    if token_match:
        token = token_match.group(1)
        for order in orders:
            if str(order.id).replace("-", "").startswith(token.replace("-", "")):
                return order
    return orders[0] if len(orders) == 1 else None


def _first_int(message: str) -> int | None:
    match = re.search(r"\b(\d+)\b", message.replace(",", ""))
    return int(match.group(1)) if match else None


def _price_from_message(message: str) -> float | None:
    text = message.lower().replace(",", "")
    match = re.search(r"(?:price|ngn|₦)\s*(\d+(?:\.\d+)?)", text)
    if match:
        return float(match.group(1))
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    return float(numbers[0]) if numbers else None


def _stock_from_message(message: str) -> int | None:
    match = re.search(r"(?:stock|qty|quantity)\s*(\d+)", message.lower().replace(",", ""))
    return int(match.group(1)) if match else None


def _product_name_from_create_message(message: str) -> str:
    text = re.sub(r"\b(add|create|new)\s+product\b", "", message, flags=re.IGNORECASE).strip()
    text = re.split(r"\b(price|ngn|stock|qty|quantity)\b", text, flags=re.IGNORECASE)[0].strip(" :-")
    return text[:150]


async def get_bizprint(db: AsyncSession, user_id: str):
    snapshot = (await db.execute(
        select(BizPrintSnapshot).where(BizPrintSnapshot.user_id == user_id).order_by(BizPrintSnapshot.created_at.desc())
    )).scalar_one_or_none()
    return snapshot.snapshot_json if snapshot else {}


async def initiate_withdrawal(db: AsyncSession, user_id: str, amount: float):
    token, session = await create_flow_session(db, user_id, "withdrawal", {"amount": amount})
    await emit_event(db, {
        "event_type": "withdrawal_requested",
        "source": "whatsapp",
        "user_id": user_id,
        "amount": amount,
        "flow_session_id": str(session.id),
    }, process_now=False)
    return {"requires_pin": True, "flow_token": token, "amount": float(Decimal(str(amount)))}


async def parse_receipt(image_url: str):
    return {"image_url": image_url, "status": "queued_for_review"}


async def send_whatsapp_notification(user_id: str, message: str):
    return {"queued": True, "user_id": user_id, "message": message}


async def get_marketing_analytics_tool(db: AsyncSession, user_id: str, days: int = 7):
    from app.campaigns.routes import get_marketing_analytics
    store = await get_store_by_user(db, user_id)
    if not store:
        return {"error": "Store not found"}
    return await get_marketing_analytics(str(store.id), days=days, db=db)


AVAILABLE_TOOL_NAMES = [
    "get_store_by_user",
    "get_store_orders",
    "get_recent_orders",
    "get_pending_orders",
    "get_today_sales",
    "get_low_stock_products",
    "get_top_products",
    "get_store_link",
    "create_product_from_chat_message",
    "update_inventory",
    "update_inventory_from_chat",
    "mark_order_fulfilled_from_chat",
    "generate_store_insight",
    "get_bizprint",
    "initiate_withdrawal",
    "parse_receipt",
    "create_flow_session",
    "send_whatsapp_notification",
    "get_marketing_analytics_tool",
    "emit_event",
]
