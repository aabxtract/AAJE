from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import Order, Product, Store
from app.models.intelligence import ScoreEvent
from app.models.score import Score
from app.models.transaction import Transaction
from app.models.vault import Vault


async def recalculate_user_score(db: AsyncSession, user_id) -> Score:
    transactions = (await db.execute(select(Transaction).where(Transaction.user_id == user_id))).scalars().all()
    stores = (await db.execute(select(Store).where(Store.user_id == user_id))).scalars().all()
    store_ids = [store.id for store in stores]
    orders = []
    products = []
    if store_ids:
        orders = (await db.execute(select(Order).where(Order.store_id.in_(store_ids)))).scalars().all()
        products = (await db.execute(select(Product).where(Product.store_id.in_(store_ids)))).scalars().all()
    vaults = (await db.execute(select(Vault).where(Vault.user_id == user_id))).scalars().all()

    paid_orders = [order for order in orders if order.payment_status == "paid"]
    verified_tx = [tx for tx in transactions if tx.provider == "squad" or tx.source == "squad"]
    total_sales = sum(Decimal(order.total_amount or 0) for order in paid_orders)
    has_squad_store = any(store.has_squad_account for store in stores)

    activity_score = min(35, len(paid_orders) * 4 + len(verified_tx) * 2)
    commerce_score = min(25, len(products) * 2 + len(stores) * 5)
    money_score = min(25, int(total_sales / Decimal("10000")) + len(vaults) * 3)
    quality_score = 15 if has_squad_store and verified_tx else 7 if has_squad_store or verified_tx else 0
    total = min(100, activity_score + commerce_score + money_score + quality_score)

    score = (await db.execute(select(Score).where(Score.user_id == user_id))).scalar_one_or_none()
    if not score:
        score = Score(user_id=user_id)
        db.add(score)
        await db.flush()

    score.trader_score = float(total)
    score.credit_grade = _grade(total)
    score.data_quality = _data_quality(has_squad_store, len(verified_tx), len(paid_orders))
    score.volume_score = float(min(25, money_score))
    score.consistency_score = float(min(25, activity_score))
    score.savings_score = float(min(25, len(vaults) * 5))
    score.tenure_score = float(min(25, len(stores) * 5 + len(products)))
    score.recommended_loan_ceiling = _loan_ceiling(total, total_sales)

    db.add(ScoreEvent(
        user_id=user_id,
        score=score.trader_score,
        grade=score.credit_grade,
        factors_json={
            "paid_orders": len(paid_orders),
            "verified_squad_transactions": len(verified_tx),
            "product_count": len(products),
            "store_count": len(stores),
            "vault_count": len(vaults),
            "total_sales": float(total_sales),
            "data_quality": score.data_quality,
        },
    ))
    return score


def _grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 50:
        return "C"
    if score >= 30:
        return "D"
    return "E"


def _data_quality(has_squad_store: bool, verified_transactions: int, paid_orders: int) -> str:
    if has_squad_store and verified_transactions >= 10 and paid_orders >= 5:
        return "high"
    if has_squad_store or verified_transactions >= 3 or paid_orders >= 3:
        return "medium"
    return "low"


def _loan_ceiling(score: float, total_sales: Decimal) -> Decimal:
    if score < 40:
        return Decimal("0")
    multiplier = Decimal("0.15") if score < 60 else Decimal("0.25") if score < 80 else Decimal("0.35")
    return min(Decimal("2000000"), total_sales * multiplier)
