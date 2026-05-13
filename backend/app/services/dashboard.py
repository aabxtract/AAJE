from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.bizprint import generate_bizprint
from app.intelligence.insights import generate_store_insights
from app.intelligence.scorer import recalculate_user_score
from app.models.commerce import Order, Product, Store
from app.models.transaction import Transaction


async def get_owner_overview(db: AsyncSession, user_id: str) -> dict:
    stores = (await db.execute(select(Store).where(Store.user_id == user_id))).scalars().all()
    store_ids = [store.id for store in stores]
    products = []
    orders = []
    if store_ids:
        products = (await db.execute(select(Product).where(Product.store_id.in_(store_ids)))).scalars().all()
        orders = (await db.execute(select(Order).where(Order.store_id.in_(store_ids)).order_by(Order.created_at.desc()))).scalars().all()
    transactions = (await db.execute(select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.timestamp.desc()))).scalars().all()
    score = await recalculate_user_score(db, user_id)
    bizprint = await generate_bizprint(db, user_id, store_ids[0] if len(store_ids) == 1 else None)

    paid_orders = [order for order in orders if order.payment_status == "paid"]
    low_stock = [product for product in products if (product.stock_quantity or 0) <= (product.low_stock_threshold or 0)]
    primary_store = stores[0] if stores else None
    insights = await generate_store_insights(db, primary_store.id) if primary_store else {"summary": "Create a store to start building your business identity.", "alerts": [], "actions": []}

    return {
        "stores": [
            {
                "id": str(store.id),
                "name": store.store_name,
                "slug": store.slug,
                "link": f"/s/{store.slug}",
                "has_squad_account": store.has_squad_account,
            }
            for store in stores
        ],
        "metrics": {
            "store_count": len(stores),
            "product_count": len(products),
            "order_count": len(orders),
            "paid_order_count": len(paid_orders),
            "total_sales": float(sum(order.total_amount or 0 for order in paid_orders)),
            "low_stock_count": len(low_stock),
            "transaction_count": len(transactions),
        },
        "recent_orders": [
            {
                "id": str(order.id),
                "store_id": str(order.store_id),
                "customer_name": order.customer_name,
                "total_amount": float(order.total_amount or 0),
                "payment_status": order.payment_status,
                "order_status": order.order_status,
                "created_at": str(order.created_at),
            }
            for order in orders[:8]
        ],
        "low_stock": [
            {"id": str(product.id), "name": product.name, "stock_quantity": product.stock_quantity, "threshold": product.low_stock_threshold}
            for product in low_stock[:8]
        ],
        "score": {
            "value": float(score.trader_score or 0),
            "grade": score.credit_grade,
            "data_quality": score.data_quality,
            "recommended_loan_range": float(score.recommended_loan_ceiling or 0),
        },
        "bizprint": {
            "data_quality": bizprint.data_quality,
            "snapshot": bizprint.snapshot_json,
        },
        "insights": insights,
    }
