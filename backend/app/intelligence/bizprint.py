from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import Order, Product, Store
from app.models.intelligence import BizPrintSnapshot
from app.models.score import Score
from app.models.transaction import Transaction


async def generate_bizprint(db: AsyncSession, user_id, store_id=None) -> BizPrintSnapshot:
    stores_query = select(Store).where(Store.user_id == user_id)
    if store_id:
        stores_query = stores_query.where(Store.id == store_id)
    stores = (await db.execute(stores_query)).scalars().all()
    store_ids = [store.id for store in stores]
    products = []
    orders = []
    if store_ids:
        products = (await db.execute(select(Product).where(Product.store_id.in_(store_ids)))).scalars().all()
        orders = (await db.execute(select(Order).where(Order.store_id.in_(store_ids)))).scalars().all()
    transactions = (await db.execute(select(Transaction).where(Transaction.user_id == user_id))).scalars().all()
    score = (await db.execute(select(Score).where(Score.user_id == user_id))).scalar_one_or_none()

    paid_orders = [order for order in orders if order.payment_status == "paid"]
    total_sales = sum(float(order.total_amount or 0) for order in paid_orders)
    low_stock_count = len([product for product in products if (product.stock_quantity or 0) <= (product.low_stock_threshold or 0)])
    has_squad_account = any(store.has_squad_account for store in stores)
    verified_payments = len([tx for tx in transactions if tx.provider == "squad" or tx.source == "squad"])
    data_quality = _data_quality(has_squad_account, verified_payments, len(paid_orders), len(products))

    snapshot = BizPrintSnapshot(
        user_id=user_id,
        store_id=store_id,
        data_quality=data_quality,
        snapshot_json={
            "identity_type": "business_activity",
            "data_quality": data_quality,
            "stores": [{"id": str(store.id), "name": store.store_name, "slug": store.slug} for store in stores],
            "activity": {
                "product_count": len(products),
                "order_count": len(orders),
                "paid_order_count": len(paid_orders),
                "verified_squad_payments": verified_payments,
                "total_sales": total_sales,
                "low_stock_count": low_stock_count,
            },
            "score": {
                "value": float(score.trader_score or 0) if score else 0,
                "grade": score.credit_grade if score else None,
                "recommended_loan_range": float(score.recommended_loan_ceiling or 0) if score else 0,
            },
            "strengths": _strengths(has_squad_account, verified_payments, len(products), len(paid_orders)),
            "next_best_actions": _next_best_actions(has_squad_account, verified_payments, len(products), low_stock_count),
        },
    )
    db.add(snapshot)
    await db.flush()
    return snapshot


def _data_quality(has_squad_account: bool, verified_payments: int, paid_orders: int, products: int) -> str:
    if has_squad_account and verified_payments >= 10 and paid_orders >= 5 and products >= 3:
        return "high"
    if has_squad_account or verified_payments >= 3 or paid_orders >= 3:
        return "medium"
    return "low"


def _strengths(has_squad_account: bool, verified_payments: int, products: int, paid_orders: int) -> list[str]:
    strengths = []
    if has_squad_account:
        strengths.append("Squad-connected business account")
    if verified_payments:
        strengths.append("Verified digital payment activity")
    if products >= 3:
        strengths.append("Structured product catalogue")
    if paid_orders >= 3:
        strengths.append("Repeat storefront order activity")
    return strengths or ["Business profile started"]


def _next_best_actions(has_squad_account: bool, verified_payments: int, products: int, low_stock_count: int) -> list[str]:
    actions = []
    if not has_squad_account:
        actions.append("Connect a Squad account to improve payment verification")
    if products < 3:
        actions.append("Add more products or services to strengthen your storefront")
    if verified_payments < 3:
        actions.append("Receive more store payments through AAJE/Squad")
    if low_stock_count:
        actions.append("Restock low inventory items")
    return actions or ["Keep receiving verified orders through your storefront"]
