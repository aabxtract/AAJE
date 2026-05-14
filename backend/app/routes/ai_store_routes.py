from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ai_store_builder import generate_store_payload, create_store

router = APIRouter(prefix="/ai/store", tags=["ai_store"])


@router.post("/build")
async def build_store(payload: Dict[str, Any]):
    """Generate a suggested store payload from user input (no DB side effects)."""
    suggestion = await generate_store_payload(payload)
    return suggestion


@router.post("/create")
async def create_store_endpoint(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Create a store and starter products in the database.

    Expected payload:
    {
      "user_id": "<uuid>",
      "store_payload": { ... },
      "create_products": true
    }
    """
    user_id = payload.get("user_id")
    store_payload = payload.get("store_payload")
    if not user_id or not store_payload:
        raise HTTPException(status_code=400, detail="user_id and store_payload are required")

    store = await create_store(db, user_id, store_payload, create_products=payload.get("create_products", True))
    return {"store_id": str(store.id), "slug": store.slug}
