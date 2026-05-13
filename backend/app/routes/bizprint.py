from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.intelligence.bizprint import generate_bizprint
from app.intelligence.scorer import recalculate_user_score
from app.models.intelligence import ScoreEvent
from app.models.user import User

router = APIRouter(prefix="/bizprint", tags=["bizprint"])


@router.get("/{user_id}")
async def get_bizprint(user_id: str, db: AsyncSession = Depends(get_db)):
    if not await db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    score = await recalculate_user_score(db, user_id)
    snapshot = await generate_bizprint(db, user_id)
    return {
        "trader_score": float(score.trader_score or 0),
        "credit_grade": score.credit_grade,
        "consistency_score": float(score.consistency_score or 0),
        "volume_score": float(score.volume_score or 0),
        "savings_score": float(score.savings_score or 0),
        "tenure_score": float(score.tenure_score or 0),
        "recommended_loan_ceiling": float(score.recommended_loan_ceiling or 0),
        "data_quality": score.data_quality,
        "snapshot": snapshot.snapshot_json,
    }


@router.get("/{user_id}/history")
async def bizprint_history(user_id: str, db: AsyncSession = Depends(get_db)):
    events = (await db.execute(
        select(ScoreEvent).where(ScoreEvent.user_id == user_id).order_by(ScoreEvent.created_at.desc()).limit(12)
    )).scalars().all()
    return [
        {
            "score": float(event.score or 0),
            "grade": event.grade,
            "factors": event.factors_json,
            "created_at": event.created_at,
        }
        for event in events
    ]
