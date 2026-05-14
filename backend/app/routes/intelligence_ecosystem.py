from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.bizprint import generate_bizprint
from app.database import get_db
from app.intelligence.context_builder import build_context
from app.intelligence.scorer import recalculate_user_score
from app.models.commerce import Store
from app.models.intelligence import BizPrintSnapshot
from app.models.user import User
from app.events.handlers import emit_event

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


@router.get("/user/{user_id}")
async def user_intelligence(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await build_context(db, user)


@router.get("/store/{store_id}")
async def store_intelligence(store_id: str, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    user = await db.get(User, store.user_id)
    return await build_context(db, user, "storefront_extension")


@router.get("/bizprint/{user_id}")
async def bizprint(user_id: str, db: AsyncSession = Depends(get_db)):
    snapshot = (await db.execute(
        select(BizPrintSnapshot).where(BizPrintSnapshot.user_id == user_id).order_by(BizPrintSnapshot.created_at.desc())
    )).scalar_one_or_none()
    if not snapshot:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        score = await recalculate_user_score(db, user_id)
        snapshot = await generate_bizprint(db, user_id)
        return {
            "data_quality": snapshot.data_quality,
            "snapshot": snapshot.snapshot_json,
            "score": {"value": float(score.trader_score or 0), "grade": score.credit_grade},
            "created_at": snapshot.created_at,
        }
    return {"data_quality": snapshot.data_quality, "snapshot": snapshot.snapshot_json, "created_at": snapshot.created_at}


@router.post("/recalculate-score")
async def recalculate_score(user_id: str, db: AsyncSession = Depends(get_db)):
    if not await db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    score = await recalculate_user_score(db, user_id)
    snapshot = await generate_bizprint(db, user_id)
    event = await emit_event(db, {
        "event_type": "score_updated",
        "source": "squad_intelligence",
        "user_id": user_id,
    }, process_now=False)
    return {
        "status": "recalculated",
        "event_id": str(event.id),
        "score": {
            "value": float(score.trader_score or 0),
            "grade": score.credit_grade,
            "data_quality": score.data_quality,
            "recommended_loan_range": float(score.recommended_loan_ceiling or 0),
        },
        "bizprint_snapshot_id": str(snapshot.id),
    }
