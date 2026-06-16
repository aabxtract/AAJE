from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification_log import NotificationLog
from app.models.store import Store
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: UUID
    type: str | None = None
    channel: str | None = None
    message: str | None = None
    delivered: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    store = await db.scalar(select(Store).where(Store.user_id == user.id))
    where = [NotificationLog.user_id == user.id]
    if store:
        where.append(NotificationLog.business_id == store.id)
    rows = (
        await db.execute(
            select(NotificationLog)
            .where(*where)
            .order_by(NotificationLog.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    for row in rows:
        row.message = row.message or row.content
    return [NotificationResponse.model_validate(row) for row in rows]


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    row = await db.get(NotificationLog, notification_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.delivered = True
    await db.commit()
    await db.refresh(row)
    row.message = row.message or row.content
    return NotificationResponse.model_validate(row)
