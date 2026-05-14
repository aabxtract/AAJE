import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product


async def create_product(session: AsyncSession, store_id: uuid.UUID, data: dict) -> Product:
    p = Product(
        store_id=store_id,
        name=data.get("name"),
        description=data.get("description"),
        category=data.get("category"),
        price=data.get("price", 0),
        image_url=data.get("image_url"),
        stock_quantity=data.get("stock_quantity", 0),
        low_stock_threshold=data.get("low_stock_threshold", 0),
        is_active=data.get("is_active", True),
    )
    session.add(p)
    await session.flush()
    return p


async def list_products(session: AsyncSession, store_id: uuid.UUID) -> List[Product]:
    q = select(Product).where(Product.store_id == store_id)
    res = await session.execute(q)
    return res.scalars().all()


async def get_product(session: AsyncSession, product_id: uuid.UUID) -> Product:
    q = select(Product).where(Product.id == product_id)
    res = await session.execute(q)
    return res.scalar_one_or_none()
