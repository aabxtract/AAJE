from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import Order, Product, Store
from app.models.income_stream import IncomeStream
from app.models.intelligence import BizPrintSnapshot
from app.models.money import Wallet
from app.models.score import Score
from app.models.transaction import Transaction
from app.models.user import User
from app.models.vault import Vault


async def determine_persona(db: AsyncSession, user: User) -> str:
    store = (await db.execute(select(Store).where(Store.user_id == user.id))).scalar_one_or_none()
    if store:
        return "storefront_extension"
    return user.persona_mode or "normal_business_manager"


async def build_context(db: AsyncSession, user: User, persona: str | None = None) -> dict:
    persona = persona or await determine_persona(db, user)
    base = {
        "persona": persona,
        "user": {
            "id": str(user.id),
            "name": user.full_name,
            "phone": user.whatsapp_no,
            "language": user.preferred_language or "en",
        },
    }
    if persona == "storefront_extension":
        base.update(await _storefront_context(db, user))
    else:
        base.update(await _business_manager_context(db, user))
    return base


async def _storefront_context(db: AsyncSession, user: User) -> dict:
    stores = (await db.execute(select(Store).where(Store.user_id == user.id))).scalars().all()
    store = stores[0] if stores else None
    if not store:
        return {"store": None, "products": [], "orders": [], "sales": {}, "recent_alerts": []}

    products = (await db.execute(select(Product).where(Product.store_id == store.id))).scalars().all()
    orders = (await db.execute(select(Order).where(Order.store_id == store.id).order_by(Order.created_at.desc()))).scalars().all()
    transactions = (await db.execute(select(Transaction).where(Transaction.store_id == store.id).order_by(Transaction.timestamp.desc()))).scalars().all()
    score = (await db.execute(select(Score).where(Score.user_id == user.id))).scalar_one_or_none()
    vault_rows = (await db.execute(select(Vault).where(Vault.user_id == user.id))).scalars().all()
    wallet = (await db.execute(select(Wallet).where(Wallet.user_id == user.id))).scalar_one_or_none()
    latest_bizprint = (await db.execute(
        select(BizPrintSnapshot).where(BizPrintSnapshot.store_id == store.id).order_by(BizPrintSnapshot.created_at.desc())
    )).scalar_one_or_none()

    today = datetime.now(timezone.utc).date()
    paid_today = [
        order for order in orders
        if order.payment_status == "paid" and order.paid_at and order.paid_at.date() == today
    ]
    return {
        "store": {
            "id": str(store.id),
            "name": store.store_name,
            "slug": store.slug,
            "link": f"/s/{store.slug}",
            "has_squad_account": store.has_squad_account,
            "squad_virtual_account_number": store.squad_virtual_account_number,
        },
        "products": [
            {
                "id": str(product.id),
                "name": product.name,
                "category": product.category,
                "price": float(product.price or 0),
                "stock_quantity": product.stock_quantity or 0,
                "low_stock_threshold": product.low_stock_threshold or 0,
            }
            for product in products
        ],
        "orders": [
            {
                "id": str(order.id),
                "customer_name": order.customer_name,
                "total_amount": float(order.total_amount or 0),
                "payment_status": order.payment_status,
                "order_status": order.order_status,
                "created_at": str(order.created_at),
            }
            for order in orders[:10]
        ],
        "sales": {
            "today_amount": float(sum(order.total_amount or 0 for order in paid_today)),
            "today_count": len(paid_today),
            "total_paid_amount": float(sum(order.total_amount or 0 for order in orders if order.payment_status == "paid")),
        },
        "transactions": [{"amount": float(tx.amount), "type": tx.type, "source": tx.source} for tx in transactions[:10]],
        "score": _score_payload(score),
        "vaults": [{"id": str(v.id), "name": v.name, "balance": float(v.current_balance or 0)} for v in vault_rows],
        "wallet": _wallet_payload(wallet),
        "bizprint": latest_bizprint.snapshot_json if latest_bizprint else None,
        "recent_alerts": [
            {"type": "inventory_low", "product": p.name, "stock_quantity": p.stock_quantity}
            for p in products if (p.stock_quantity or 0) <= (p.low_stock_threshold or 0)
        ],
    }


async def _business_manager_context(db: AsyncSession, user: User) -> dict:
    streams = (await db.execute(select(IncomeStream).where(IncomeStream.user_id == user.id))).scalars().all()
    vaults = (await db.execute(select(Vault).where(Vault.user_id == user.id))).scalars().all()
    wallet = (await db.execute(select(Wallet).where(Wallet.user_id == user.id))).scalar_one_or_none()
    transactions = (await db.execute(select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.timestamp.desc()))).scalars().all()
    score = (await db.execute(select(Score).where(Score.user_id == user.id))).scalar_one_or_none()
    return {
        "business_streams": [{"id": str(stream.id), "name": stream.stream_name, "type": stream.stream_type} for stream in streams],
        "vaults": [{"id": str(vault.id), "name": vault.name, "balance": float(vault.current_balance or 0)} for vault in vaults],
        "wallet": _wallet_payload(wallet),
        "transactions": [
            {"amount": float(tx.amount), "type": tx.type, "narration": tx.narration, "source": tx.source, "date": str(tx.timestamp)}
            for tx in transactions[:10]
        ],
        "score": _score_payload(score),
        "receipt_records": [],
        "reports": {"recent_transaction_count": len(transactions)},
    }


def _score_payload(score: Score | None) -> dict:
    if not score:
        return {"score": 0, "grade": None, "data_quality": "low", "recommended_loan_range": None}
    return {
        "score": float(score.trader_score or 0),
        "grade": score.credit_grade,
        "data_quality": score.data_quality,
        "recommended_loan_range": float(score.recommended_loan_ceiling or 0),
    }


def _wallet_payload(wallet: Wallet | None) -> dict:
    if not wallet:
        return {"available_balance": 0, "total_earned": 0, "total_withdrawn": 0}
    return {
        "available_balance": float(wallet.available_balance or 0),
        "total_earned": float(wallet.total_earned or 0),
        "total_withdrawn": float(wallet.total_withdrawn or 0),
    }
