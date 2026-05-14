from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import Order, Product, Store
from app.models.intelligence import BizPrintSnapshot
from app.models.score import Score
from app.models.transaction import Transaction
from app.models.vault import Vault
from app.services.events import emit_event
from app.services.flows import create_flow_session
from app.services.storefront import create_product


async def get_store_by_user(db: AsyncSession, user_id: str):
    return (await db.execute(select(Store).where(Store.user_id == user_id))).scalar_one_or_none()


async def get_store_orders(db: AsyncSession, store_id: str):
    return (await db.execute(select(Order).where(Order.store_id == store_id).order_by(Order.created_at.desc()))).scalars().all()


async def get_today_sales(db: AsyncSession, store_id: str):
    today = datetime.now(timezone.utc).date()
    orders = await get_store_orders(db, store_id)
    paid = [order for order in orders if order.payment_status == "paid" and order.paid_at and order.paid_at.date() == today]
    return {"count": len(paid), "amount": float(sum(order.total_amount or 0 for order in paid))}


async def get_low_stock_products(db: AsyncSession, store_id: str):
    result = await db.execute(select(Product).where(Product.store_id == store_id))
    return [p for p in result.scalars().all() if (p.stock_quantity or 0) <= (p.low_stock_threshold or 0)]


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


async def generate_store_insight(db: AsyncSession, store_id: str):
    sales = await get_today_sales(db, store_id)
    low_stock = await get_low_stock_products(db, store_id)
    return f"Today you have {sales['count']} paid order(s) worth NGN {sales['amount']:,.2f}. {len(low_stock)} product(s) are low in stock."


async def get_vault_balances(db: AsyncSession, user_id: str):
    vaults = (await db.execute(select(Vault).where(Vault.user_id == user_id))).scalars().all()
    return [{"name": vault.name, "balance": float(vault.current_balance or 0)} for vault in vaults]


async def get_recent_transactions(db: AsyncSession, user_id: str):
    txs = (await db.execute(select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.timestamp.desc()))).scalars().all()
    return [{"amount": float(tx.amount), "type": tx.type, "source": tx.source, "reference": tx.squad_transaction_ref} for tx in txs[:10]]


async def get_score(db: AsyncSession, user_id: str):
    score = (await db.execute(select(Score).where(Score.user_id == user_id))).scalar_one_or_none()
    if not score:
        return {"score": 0, "grade": None, "data_quality": "low"}
    return {"score": float(score.trader_score or 0), "grade": score.credit_grade, "data_quality": score.data_quality}


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


async def generate_financial_insight(db: AsyncSession, user_id: str):
    txs = await get_recent_transactions(db, user_id)
    credits = sum(tx["amount"] for tx in txs if tx["type"] == "credit")
    debits = sum(tx["amount"] for tx in txs if tx["type"] == "debit")
    return f"Your recent credits are NGN {credits:,.2f}, and recent debits are NGN {debits:,.2f}."


async def send_account_number(db: AsyncSession, user_id: str):
    store = await get_store_by_user(db, user_id)
    if store and store.squad_virtual_account_number:
        return store.squad_virtual_account_number
    return None


async def parse_receipt(image_url: str):
    return {"image_url": image_url, "status": "queued_for_review"}


async def send_whatsapp_notification(user_id: str, message: str):
    return {"queued": True, "user_id": user_id, "message": message}


async def get_marketing_analytics_tool(db: AsyncSession, user_id: str, days: int = 7):
    from app.routes.marketing import get_marketing_analytics
    store = await get_store_by_user(db, user_id)
    if not store:
        return {"error": "Store not found"}
    return await get_marketing_analytics(str(store.id), days=days, db=db)


AVAILABLE_TOOL_NAMES = [
    "get_store_by_user",
    "get_store_orders",
    "get_today_sales",
    "get_low_stock_products",
    "get_top_products",
    "get_store_link",
    "create_product_from_chat",
    "update_inventory",
    "generate_store_insight",
    "get_vault_balances",
    "get_recent_transactions",
    "get_score",
    "get_bizprint",
    "initiate_withdrawal",
    "generate_financial_insight",
    "send_account_number",
    "parse_receipt",
    "create_flow_session",
    "send_whatsapp_notification",
    "get_marketing_analytics_tool",
    "emit_event",
]
