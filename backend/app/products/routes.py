from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.products.service import create_product, list_products

router = APIRouter(prefix="/stores/{store_id}/products", tags=["products"])


@router.post("/")
async def add_product(store_id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    prod = await create_product(db, store_id, payload)
    return {"product_id": str(prod.id)}


@router.get("/")
async def get_products(store_id: str, db: AsyncSession = Depends(get_db)):
    prods = await list_products(db, store_id)
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "price": float(p.price) if p.price is not None else 0,
            "stock_quantity": p.stock_quantity,
        }
        for p in prods
    ]
