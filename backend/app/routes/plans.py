from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/plans", tags=["plans"])


class UpgradeRequest(BaseModel):
    user_id: str
    plan: str = "premium"


@router.post("/upgrade")
async def upgrade_plan(payload: UpgradeRequest, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # For hackathon: accept upgrade without payment
    user.plan = payload.plan
    return {"status": "upgraded", "user_id": str(user.id), "plan": user.plan}


@router.get("/current/{user_id}")
async def current_plan(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": str(user.id), "plan": getattr(user, "plan", "free")}
