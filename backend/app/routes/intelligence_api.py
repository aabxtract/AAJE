from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import desc, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.income_stream import IncomeStream
from app.models.score import Score
from app.models.user import User

router = APIRouter()
bearer = HTTPBearer()


def _authorize(credentials: HTTPAuthorizationCredentials = Security(bearer)):
    if credentials.credentials != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid token")


@router.get("/economic-score/{user_id}")
async def economic_score(user_id: str, _: None = Security(_authorize)):
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if not user or not user.onboarding_complete:
            raise HTTPException(status_code=404, detail="User not found")
        score_result = await db.execute(
            select(Score).where(Score.user_id == user_id).order_by(desc(Score.computed_at))
        )
        score = score_result.scalar_one_or_none()
        if not score:
            raise HTTPException(status_code=404, detail="Score not found")
        stream_result = await db.execute(select(IncomeStream).where(IncomeStream.user_id == user_id))
        active_streams = len(stream_result.scalars().all())

    created_at = user.created_at or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    tenure_days = max((datetime.now(timezone.utc) - created_at).days, 0)
    reliability = "high" if score.trader_score >= 70 else "medium" if score.trader_score >= 50 else "low"
    return {
        "trader_score": score.trader_score,
        "credit_grade": score.credit_grade,
        "transaction_consistency": round((score.consistency_score or 0) / 25, 2),
        "estimated_income_reliability": reliability,
        "suggested_credit_threshold": float(score.recommended_loan_ceiling or 0),
        "active_streams": active_streams,
        "data_source": "squad_verified",
        "tenure_days": tenure_days,
    }
