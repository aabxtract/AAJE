from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import Order, Product, Store


async def generate_store_insights(db: AsyncSession, store_id) -> dict:
    store = await db.get(Store, store_id)
    if not store:
        return {"summary": "Store not found.", "alerts": [], "actions": []}

    products = (await db.execute(select(Product).where(Product.store_id == store_id))).scalars().all()
    orders = (await db.execute(select(Order).where(Order.store_id == store_id))).scalars().all()
    paid_orders = [order for order in orders if order.payment_status == "paid"]
    pending_orders = [order for order in orders if order.payment_status != "paid"]
    low_stock = [product for product in products if (product.stock_quantity or 0) <= (product.low_stock_threshold or 0)]

    today = datetime.now(timezone.utc).date()
    paid_today = [order for order in paid_orders if order.paid_at and order.paid_at.date() == today]
    today_sales = sum(float(order.total_amount or 0) for order in paid_today)
    total_sales = sum(float(order.total_amount or 0) for order in paid_orders)

    alerts = []
    if low_stock:
        alerts.append({"type": "inventory_low", "count": len(low_stock), "products": [product.name for product in low_stock[:5]]})
    if pending_orders:
        alerts.append({"type": "pending_orders", "count": len(pending_orders)})

    actions = []
    if low_stock:
        actions.append("Restock low inventory products")
    if not store.has_squad_account:
        actions.append("Connect a Squad account for verified payments and stronger BizPrint")
    if len(products) < 3:
        actions.append("Add more products or services to improve storefront completeness")

    return {
        "summary": f"{store.store_name} has {len(paid_today)} paid order(s) today worth NGN {today_sales:,.2f}. Total verified store sales are NGN {total_sales:,.2f}.",
        "metrics": {
            "today_paid_orders": len(paid_today),
            "today_sales": today_sales,
            "total_paid_orders": len(paid_orders),
            "total_sales": total_sales,
            "pending_orders": len(pending_orders),
            "product_count": len(products),
            "low_stock_count": len(low_stock),
        },
        "alerts": alerts,
        "actions": actions or ["Keep sharing your store link and receiving verified payments"],
    }
