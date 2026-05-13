from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.intelligence.bizprint import generate_bizprint
from app.intelligence.insights import generate_store_insights
from app.intelligence.scorer import recalculate_user_score
from app.models.commerce import Order, Product, Store
from app.models.user import User
from app.services.dashboard import get_owner_overview

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview/{user_id}")
async def overview(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await get_owner_overview(db, user_id)


@router.get("/stores/{user_id}")
async def stores(user_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Store).where(Store.user_id == user_id))).scalars().all()
    return [
        {
            "id": str(store.id),
            "name": store.store_name,
            "slug": store.slug,
            "link": f"/s/{store.slug}",
            "description": store.description,
            "tagline": store.tagline,
            "theme_json": store.theme_json,
            "has_squad_account": store.has_squad_account,
            "squad_virtual_account_number": store.squad_virtual_account_number,
        }
        for store in rows
    ]


@router.get("/orders/{store_id}")
async def orders(store_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Order).where(Order.store_id == store_id).order_by(Order.created_at.desc()))).scalars().all()
    return [
        {
            "id": str(order.id),
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "total_amount": float(order.total_amount or 0),
            "payment_status": order.payment_status,
            "order_status": order.order_status,
            "reference": order.squad_payment_reference,
            "created_at": order.created_at,
            "paid_at": order.paid_at,
        }
        for order in rows
    ]


@router.get("/products/{store_id}")
async def products(store_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Product).where(Product.store_id == store_id).order_by(Product.created_at.desc()))).scalars().all()
    return [
        {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "price": float(product.price or 0),
            "image_url": product.image_url,
            "stock_quantity": product.stock_quantity,
            "low_stock_threshold": product.low_stock_threshold,
            "is_low_stock": (product.stock_quantity or 0) <= (product.low_stock_threshold or 0),
            "is_active": product.is_active,
        }
        for product in rows
    ]


@router.get("/insights/{store_id}")
async def insights(store_id: str, db: AsyncSession = Depends(get_db)):
    if not await db.get(Store, store_id):
        raise HTTPException(status_code=404, detail="Store not found")
    return await generate_store_insights(db, store_id)


@router.get("/bizprint/{user_id}")
async def dashboard_bizprint(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    score = await recalculate_user_score(db, user_id)
    snapshot = await generate_bizprint(db, user_id)
    return {
        "score": {
            "value": float(score.trader_score or 0),
            "grade": score.credit_grade,
            "data_quality": score.data_quality,
            "recommended_loan_range": float(score.recommended_loan_ceiling or 0),
        },
        "bizprint": {
            "data_quality": snapshot.data_quality,
            "snapshot": snapshot.snapshot_json,
            "created_at": snapshot.created_at,
        },
    }
