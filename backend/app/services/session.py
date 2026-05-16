from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.commerce import InventoryMovement, Order, OrderItem, Product, Store
from app.models.intelligence import BizPrintSnapshot
from app.models.marketing import CampaignConversion, CampaignLink, CampaignVisit
from app.models.money import Wallet
from app.models.user import User
from app.redis import clear_session, clear_state_history, get_session, save_session
from app.services.flows import create_flow_session
from app.storefront.service import create_product
from app.whatsapp.recipients import normalize_whatsapp_number, seller_notification_recipients
from app.whatsapp.service import send_text

"""
WhatsApp storefront operations router.

This is a clean replacement for the old WhatsApp bot flow. It does not run AI
reasoning, onboarding, vault flows, supplier payments, or chat-based banking.
WhatsApp is only an operational extension of the AAJE storefront.
"""

RESET_COMMANDS = {"restart", "reset", "start over", "start again", "begin again"}
BACK_COMMANDS = {"back", "undo", "go back", "previous", "prev", "return"}

HELP_TEXT = (
    "AAJE WhatsApp runs storefront operations.\n\n"
    "Try:\n"
    "- store link\n"
    "- what sold today\n"
    "- recent orders\n"
    "- pending orders\n"
    "- low stock\n"
    "- update stock Ankara Bag 12\n"
    "- add product Ankara Bag price 15000 stock 8\n"
    "- mark order 12345678 fulfilled\n"
    "- withdraw 25000\n"
    "- campaign performance\n"
    "- BizPrint summary"
)

FREE_TEXT = (
    "AAJE on WhatsApp is connected to your storefront.\n\n"
    "Ask about sales, orders, inventory, products, fulfillment, your store link, or BizPrint."
)

NOT_CONNECTED_TEXT = (
    "Connect your AAJE account to use AAJE on WhatsApp.\n\n"
    "After connecting, you can ask about sales, orders, inventory, and your storefront."
)


async def route_message(whatsapp_no: str, message: str):
    message = (message or "").strip()
    if not message:
        return

    if message.lower() in RESET_COMMANDS:
        await clear_session(whatsapp_no)
        await clear_state_history(whatsapp_no)

    async with AsyncSessionLocal() as db:
        user, store = await _connection(db, whatsapp_no)
        if not user:
            frontend = (settings.frontend_url or settings.app_public_url or "http://localhost:5173").rstrip("/")
            url = f"{frontend}/signup?wa={normalize_whatsapp_number(whatsapp_no) or whatsapp_no}"
            
            try:
                from app.whatsapp.service import send_cta_button
                await send_cta_button(
                    to=whatsapp_no,
                    body=NOT_CONNECTED_TEXT,
                    button_label="Connect AAJE",
                    url=url
                )
            except Exception:
                # Fallback if Meta credentials are not fully configured
                await send_text(whatsapp_no, f"{NOT_CONNECTED_TEXT}\n\nLink: {url}")
            return
            
        if not store:
            frontend = (settings.frontend_url or "http://localhost:5173").rstrip("/")
            await send_text(
                whatsapp_no,
                "Your AAJE account is connected. Create or publish a storefront from the web dashboard first."
                f"\n\nLink: {frontend}/dashboard",
            )
            return

        session = await get_session(whatsapp_no)
        session.update({"stage": "ACTIVE", "onboarding_complete": True, "language": "en"})
        await save_session(whatsapp_no, session)

        if message.lower() in BACK_COMMANDS or _is_help(message):
            await send_text(whatsapp_no, _help_for(user))
            return

        reply = await _handle_store_operation(db, user, store, message)
        await db.commit()
        await send_text(whatsapp_no, reply)


async def route_flow_response(whatsapp_no: str, flow_response: dict):
    """Browser-flow compatibility hook.

    New WhatsApp operations use browser flows for sensitive actions. The browser
    flow stores submissions on the FlowSession record; this hook only confirms
    receipt when an older in-memory flow calls it.
    """
    await send_text(whatsapp_no, "Secure response received. AAJE will confirm the result here.")


async def _connection(db, whatsapp_no: str) -> tuple[User | None, Store | None]:
    incoming = normalize_whatsapp_number(whatsapp_no) or whatsapp_no
    user = (await db.execute(select(User).where(User.whatsapp_no == incoming))).scalar_one_or_none()
    if not user or not user.whatsapp_connected:
        demo_recipients = seller_notification_recipients()
        if incoming not in demo_recipients:
            return None, None
        row = (await db.execute(
            select(User, Store)
            .join(Store, Store.user_id == User.id)
            .where(User.whatsapp_connected.is_(True))
            .order_by(Store.created_at.desc())
        )).first()
        return (row[0], row[1]) if row else (user, None)
    store = (await db.execute(select(Store).where(Store.user_id == user.id))).scalar_one_or_none()
    if not store:
        return user, None
    if store.contact_whatsapp != incoming and incoming not in seller_notification_recipients(user=user, store=store):
        return user, None
    return user, store


def _is_help(message: str) -> bool:
    text = message.lower().strip()
    return text in {"help", "menu", "start", "hi", "hello", "hey"} or "what can you do" in text


def _help_for(user: User) -> str:
    return HELP_TEXT


async def _handle_store_operation(db, user: User, store: Store, message: str) -> str:
    text = message.lower()

    if "store link" in text or "send my store" in text or text.strip() in {"link", "my link"}:
        return f"Store link: {_store_link(store)}"

    if "sold today" in text or "sales today" in text or ("today" in text and any(term in text for term in {"sales", "orders", "revenue", "sold"})):
        return await _today_sales(db, store)
    if "recent order" in text or text in {"orders", "show orders", "latest orders"}:
        return await _orders(db, store, pending_only=False)

    if "pending order" in text or "unfulfilled" in text:
        return await _orders(db, store, pending_only=True)
    if "low stock" in text or "low inventory" in text or "what is low" in text:
        return await _low_stock(db, store)
    if _looks_like_stock_update(text):
        return await _update_stock(db, store, message)
    if "add product" in text or "new product" in text or "create product" in text:
        return await _add_product(db, store, message)
    if "fulfilled" in text or "fulfill" in text or "delivered" in text:
        return await _mark_fulfilled(db, store, message)
    if "withdraw" in text or "cash out" in text or "payout" in text:
        return await _withdrawal_link(db, user, store, message)
    if "campaign" in text or "marketing" in text or "growth" in text or "source" in text:
        return await _campaign_performance(db, store)
    if "bizprint" in text or "business profile" in text:
        return await _bizprint(db, user, store)
    if "top product" in text or "best product" in text or "fastest" in text:
        return await _top_products(db, store)
    if "summary" in text or "dashboard" in text:
        return await _dashboard_summary(db, store)

    return HELP_TEXT


def _store_link(store: Store) -> str:
    base = (settings.frontend_url or settings.app_public_url or "").rstrip("/")
    path = f"/store/{store.slug}"
    return f"{base}{path}" if base else path


async def _today_sales(db, store: Store) -> str:
    today = datetime.now(timezone.utc).date()
    orders = (await db.execute(
        select(Order)
        .where(Order.store_id == store.id, Order.payment_status == "paid")
        .order_by(Order.created_at.desc())
    )).scalars().all()
    paid_today = [
        order for order in orders
        if (order.paid_at or order.updated_at or order.created_at)
        and (order.paid_at or order.updated_at or order.created_at).date() == today
    ]
    if not paid_today:
        return "You have not sold anything today yet."
    amount = sum(Decimal(order.total_amount or 0) for order in paid_today)
    order_ids = [order.id for order in paid_today]
    rows = (await db.execute(
        select(
            OrderItem.product_name,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity"),
            func.coalesce(func.sum(OrderItem.total_price), 0).label("revenue"),
        )
        .where(OrderItem.order_id.in_(order_ids))
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
    )).all()
    lines = ["You sold today:"]
    for name, quantity, revenue in rows:
        lines.append(f"- {name or 'Product'} x{int(quantity)} - NGN {float(revenue):,.2f}")
    lines.append(f"Total sales: NGN {float(amount):,.2f}")
    return "\n".join(lines)


async def _orders(db, store: Store, pending_only: bool) -> str:
    query = select(Order).where(Order.store_id == store.id).order_by(Order.created_at.desc()).limit(6)
    rows = (await db.execute(query)).scalars().all()
    if pending_only:
        rows = [order for order in rows if order.order_status not in {"fulfilled", "delivered", "cancelled"}]
    if not rows:
        return "No pending orders." if pending_only else "No recent orders yet."
    title = "Pending orders" if pending_only else "Recent orders"
    lines = [title + ":"]
    for order in rows[:5]:
        lines.append(
            f"- {str(order.id)[:8]}: {order.customer_name or 'Customer'} - "
            f"NGN {float(order.total_amount or 0):,.2f} - {order.payment_status}/{order.order_status}"
        )
    return "\n".join(lines)


async def _low_stock(db, store: Store) -> str:
    products = (await db.execute(select(Product).where(Product.store_id == store.id))).scalars().all()
    low = [product for product in products if (product.stock_quantity or 0) <= (product.low_stock_threshold or 0)]
    if not low:
        return "No products are low in stock."
    return "Low stock:\n" + "\n".join(f"- {p.name}: {p.stock_quantity or 0} left" for p in low[:8])


def _looks_like_stock_update(text: str) -> bool:
    return any(term in text for term in {"update stock", "set stock", "add stock", "restock", "update inventory"})


async def _update_stock(db, store: Store, message: str) -> str:
    product = await _find_product(db, store, message)
    quantity = _last_int(message)
    if not product:
        return "Product not found. Send: update stock Product Name 12."
    if quantity is None:
        return "Stock quantity missing. Send: update stock Product Name 12."

    old_quantity = product.stock_quantity or 0
    text = message.lower()
    if "add stock" in text or "restock" in text:
        product.stock_quantity = old_quantity + quantity
        movement_quantity = quantity
    else:
        product.stock_quantity = max(quantity, 0)
        movement_quantity = product.stock_quantity - old_quantity

    db.add(InventoryMovement(
        store_id=store.id,
        product_id=product.id,
        movement_type="stock_added" if movement_quantity >= 0 else "stock_removed",
        quantity=abs(movement_quantity),
        reason="whatsapp_operation",
    ))
    return f"Inventory updated: {product.name} now has {product.stock_quantity} in stock."


async def _add_product(db, store: Store, message: str) -> str:
    price = _price(message)
    stock = _stock(message) or 0
    name = _product_name(message)
    if not name or price is None:
        return "Send product details like: add product Ankara Bag price 15000 stock 8."
    product = await create_product(db, store, {
        "name": name,
        "price": price,
        "stock_quantity": stock,
        "source": "whatsapp",
    })
    return f"Product added: {product.name}, NGN {float(product.price or 0):,.2f}, stock {product.stock_quantity or 0}."


async def _mark_fulfilled(db, store: Store, message: str) -> str:
    order = await _find_order(db, store, message)
    if not order:
        return "Order not found. Send: mark order 12345678 fulfilled."
    order.order_status = "fulfilled"
    order.status = "fulfilled"
    return f"Order {str(order.id)[:8]} marked fulfilled."


async def _withdrawal_link(db, user: User, store: Store, message: str) -> str:
    amount = _amount(message)
    if not amount or amount <= 0:
        return "Send the withdrawal amount. Example: withdraw 25000."
    wallet = (await db.execute(select(Wallet).where(Wallet.user_id == user.id))).scalar_one_or_none()
    available = Decimal(wallet.available_balance or 0) if wallet else Decimal("0")
    if available < Decimal(str(amount)):
        return f"Available storefront balance is NGN {float(available):,.2f}."
    token, _session = await create_flow_session(db, user.id, "withdrawal", {
        "amount": amount,
        "store_id": str(store.id),
        "whatsapp_no": user.whatsapp_no,
        "source": "whatsapp_operations",
    })
    base = (settings.app_public_url or "http://localhost:8000").rstrip("/")
    return f"Secure withdrawal link: {base}/flow?token={token}\nNo withdrawal is processed from chat."


async def _campaign_performance(db, store: Store) -> str:
    campaigns = (await db.execute(select(CampaignLink).where(CampaignLink.store_id == store.id))).scalars().all()
    if not campaigns:
        return "No campaign links yet. Create a campaign from the dashboard first."
    campaign_ids = [campaign.id for campaign in campaigns]
    visits = await db.scalar(select(func.count(CampaignVisit.id)).where(CampaignVisit.campaign_id.in_(campaign_ids))) or 0
    conversions = await db.scalar(select(func.count(CampaignConversion.id)).where(CampaignConversion.campaign_id.in_(campaign_ids))) or 0
    revenue = await db.scalar(select(func.coalesce(func.sum(CampaignConversion.revenue), 0)).where(CampaignConversion.campaign_id.in_(campaign_ids))) or 0
    return f"Campaign performance: {visits} visits, {conversions} order(s), NGN {float(revenue):,.2f} revenue."


async def _bizprint(db, user: User, store: Store) -> str:
    snapshot = (await db.execute(
        select(BizPrintSnapshot)
        .where(BizPrintSnapshot.user_id == user.id)
        .order_by(BizPrintSnapshot.created_at.desc())
    )).scalar_one_or_none()
    if not snapshot:
        return "BizPrint is not ready yet. More storefront activity will improve it."
    data = snapshot.snapshot_json or {}
    if isinstance(data, dict):
        quality = data.get("data_quality") or snapshot.data_quality
        summary = data.get("summary") or data.get("business_summary") or "Latest BizPrint snapshot is available."
        return f"BizPrint: {summary}\nData quality: {quality}."
    return f"BizPrint data quality: {snapshot.data_quality}."


async def _top_products(db, store: Store) -> str:
    rows = (await db.execute(
        select(
            OrderItem.product_name,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity"),
            func.coalesce(func.sum(OrderItem.total_price), 0).label("revenue"),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.store_id == store.id, Order.payment_status == "paid")
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
    )).all()
    if not rows:
        return "No paid product sales yet."
    return "Top products:\n" + "\n".join(
        f"- {name}: {int(quantity)} sold, NGN {float(revenue):,.2f}"
        for name, quantity, revenue in rows
    )


async def _dashboard_summary(db, store: Store) -> str:
    paid_count = await db.scalar(select(func.count(Order.id)).where(Order.store_id == store.id, Order.payment_status == "paid")) or 0
    paid_revenue = await db.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.store_id == store.id, Order.payment_status == "paid")) or 0
    product_count = await db.scalar(select(func.count(Product.id)).where(Product.store_id == store.id)) or 0
    low_count = len((await db.execute(select(Product).where(Product.store_id == store.id))).scalars().all())
    return (
        f"{store.store_name} summary:\n"
        f"- Paid orders: {paid_count}\n"
        f"- Revenue: NGN {float(paid_revenue):,.2f}\n"
        f"- Products: {product_count}\n"
        f"- Store link: {_store_link(store)}"
    )


async def _find_product(db, store: Store, message: str) -> Product | None:
    products = (await db.execute(select(Product).where(Product.store_id == store.id))).scalars().all()
    text = message.lower()
    exact = [product for product in products if product.name.lower() in text]
    if exact:
        return max(exact, key=lambda product: len(product.name))
    words = {word for word in re.sub(r"\d+", " ", text).split() if len(word) > 2}
    for product in products:
        if any(word in product.name.lower() for word in words):
            return product
    return None


async def _find_order(db, store: Store, message: str) -> Order | None:
    token = re.search(r"\b([0-9a-f]{8,})\b", message.lower())
    orders = (await db.execute(select(Order).where(Order.store_id == store.id).order_by(Order.created_at.desc()))).scalars().all()
    if token:
        value = token.group(1).replace("-", "")
        for order in orders:
            if str(order.id).replace("-", "").startswith(value):
                return order
    return orders[0] if len(orders) == 1 else None


def _amount(message: str) -> float | None:
    text = message.lower().replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", text)
    if match:
        return float(match.group(1)) * 1000
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", text)
    return float(match.group(1)) if match else None


def _last_int(message: str) -> int | None:
    numbers = re.findall(r"\b\d+\b", message.replace(",", ""))
    return int(numbers[-1]) if numbers else None


def _price(message: str) -> float | None:
    text = message.lower().replace(",", "")
    match = re.search(r"(?:price|ngn|n|₦)\s*(\d+(?:\.\d+)?)", text)
    if match:
        return float(match.group(1))
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    return float(numbers[0]) if numbers else None


def _stock(message: str) -> int | None:
    match = re.search(r"(?:stock|qty|quantity)\s*(\d+)", message.lower().replace(",", ""))
    return int(match.group(1)) if match else None


def _product_name(message: str) -> str:
    text = re.sub(r"\b(add|create|new)\s+product\b", "", message, flags=re.IGNORECASE).strip()
    text = re.split(r"\b(price|ngn|stock|qty|quantity|₦)\b", text, flags=re.IGNORECASE)[0]
    return text.strip(" :-")[:150]
