from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer
from app.models.store import Store
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/customers", tags=["customers"])


class CustomerResponse(BaseModel):
    id: UUID
    name: str
    phone: str
    total_orders: int = 0
    last_purchase: datetime | None = None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[CustomerResponse])
async def list_customers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CustomerResponse]:
    store = await _get_user_store(db, user)
    rows = (
        await db.execute(
            select(Customer)
            .where(Customer.business_id == store.id)
            .order_by(Customer.last_purchase.desc().nullslast(), Customer.created_at.desc())
        )
    ).scalars().all()
    return [CustomerResponse.model_validate(row) for row in rows]


async def _get_user_store(db: AsyncSession, user: User) -> Store:
    store = await db.scalar(select(Store).where(Store.user_id == user.id))
    if not store:
        raise HTTPException(status_code=404, detail="Complete business setup first")
    return store
