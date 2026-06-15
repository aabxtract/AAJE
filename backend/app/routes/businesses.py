from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routes.store import get_dashboard, get_my_store, setup_store, update_store
from app.schemas.store import StoreDashboardResponse, StoreResponse, StoreSetupRequest, StoreUpdateRequest
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/business", tags=["business"])


@router.post("/setup", response_model=StoreResponse)
async def setup_business(
    body: StoreSetupRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    return await setup_store(body, user, db)


@router.get("/me", response_model=StoreResponse)
async def my_business(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    return await get_my_store(user, db)


@router.patch("/me", response_model=StoreResponse)
async def update_business(
    body: StoreUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    return await update_store(body, user, db)


@router.get("/dashboard", response_model=StoreDashboardResponse)
async def business_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreDashboardResponse:
    return await get_dashboard(user, db)
