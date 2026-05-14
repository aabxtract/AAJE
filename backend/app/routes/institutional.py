from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.intelligence import Consent
from app.models.score import Score
from app.services.flows import hash_token

router = APIRouter(prefix="/api/institutional", tags=["institutional"])


@router.get("/economic-identity/{consent_token}")
async def economic_identity(consent_token: str, db: AsyncSession = Depends(get_db)):
    consent = (await db.execute(select(Consent).where(Consent.token_hash == hash_token(consent_token)))).scalar_one_or_none()
    if not consent or not consent.is_active:
        raise HTTPException(status_code=403, detail="Invalid consent")
    if consent.expires_at:
        expires_at = consent.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=403, detail="Consent expired")

    score = (await db.execute(select(Score).where(Score.user_id == consent.user_id))).scalar_one_or_none()
    return {
        "subject": "anonymous",
        "consent_type": consent.consent_type,
        "institution_id": consent.institution_id,
        "economic_identity": {
            "score_band": _score_band(float(score.trader_score or 0) if score else 0),
            "grade": score.credit_grade if score else None,
            "data_quality": score.data_quality if score else "low",
            "recommended_loan_range": float(score.recommended_loan_ceiling or 0) if score else 0,
        },
    }


def _score_band(score: float) -> str:
    if score >= 80:
        return "very_strong"
    if score >= 60:
        return "strong"
    if score >= 40:
        return "emerging"
    return "thin_file"
