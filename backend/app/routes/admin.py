from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, desc, func, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.income_stream import IncomeStream
from app.models.score import Score
from app.models.transaction import Transaction
from app.models.user import User
from app.models.vault import Vault

router = APIRouter()
_bearer = HTTPBearer()


def _require_admin(credentials: HTTPAuthorizationCredentials = Security(_bearer)):
    if credentials.credentials != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return True


def _money(value) -> float:
    return float(value or 0)


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _last4(value: str | None) -> str | None:
    return value[-4:] if value else None


@router.get("/overview", dependencies=[Depends(_require_admin)])
async def overview():
    async with AsyncSessionLocal() as db:
        total_users = await db.scalar(select(func.count()).select_from(User))
        total_transactions = await db.scalar(select(func.count()).select_from(Transaction))
        total_vault_value = await db.scalar(select(func.coalesce(func.sum(Vault.current_balance), 0)))
        average_score = await db.scalar(select(func.coalesce(func.avg(Score.trader_score), 0)))

    return {
        "total_users": int(total_users or 0),
        "total_transactions": int(total_transactions or 0),
        "total_vault_value": _money(total_vault_value),
        "average_trader_score": round(float(average_score or 0), 1),
    }


@router.get("/stats", dependencies=[Depends(_require_admin)])
async def stats_alias():
    data = await overview()
    return {
        "total_traders": data["total_users"],
        "active_today": data["total_users"],
        "transactions_today": data["total_transactions"],
        "total_vault_balance": data["total_vault_value"],
        "average_trader_score": data["average_trader_score"],
    }


@router.get("/users", dependencies=[Depends(_require_admin)])
async def list_users(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                User,
                Score.trader_score,
                Score.credit_grade,
                func.count(IncomeStream.id).label("stream_count"),
            )
            .outerjoin(Score, Score.user_id == User.id)
            .outerjoin(IncomeStream, IncomeStream.user_id == User.id)
            .group_by(User.id, Score.trader_score, Score.credit_grade)
            .order_by(desc(User.created_at))
            .limit(limit)
            .offset(offset)
        )
        total = await db.scalar(select(func.count()).select_from(User))

    users = []
    for user, trader_score, credit_grade, stream_count in result.all():
        users.append({
            "id": str(user.id),
            "whatsapp_last4": _last4(user.whatsapp_no),
            "full_name": user.full_name,
            "preferred_language": user.preferred_language,
            "onboarding_complete": bool(user.onboarding_complete),
            "trader_score": float(trader_score or 0),
            "credit_grade": credit_grade,
            "streams": int(stream_count or 0),
            "created_at": _iso(user.created_at),
        })
    return {"users": users, "total": int(total or 0)}


@router.get("/users/{user_id}", dependencies=[Depends(_require_admin)])
async def get_user(user_id: str):
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        streams_result = await db.execute(
            select(IncomeStream, Vault)
            .outerjoin(Vault, Vault.stream_id == IncomeStream.id)
            .where(IncomeStream.user_id == user.id)
            .order_by(IncomeStream.created_at)
        )
        tx_result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(desc(Transaction.timestamp))
            .limit(10)
        )
        score_result = await db.execute(select(Score).where(Score.user_id == user.id))
        score = score_result.scalar_one_or_none()

    streams = []
    for stream, vault in streams_result.all():
        streams.append({
            "id": str(stream.id),
            "stream_name": stream.stream_name,
            "stream_type": stream.stream_type,
            "split_percentage": _money(stream.split_percentage),
            "is_savings": bool(stream.is_savings),
            "is_emergency": bool(stream.is_emergency),
            "squad_account_number_last4": _last4(stream.squad_account_number),
            "current_balance": _money(vault.current_balance if vault else 0),
            "total_deposited": _money(vault.total_deposited if vault else 0),
            "total_withdrawn": _money(vault.total_withdrawn if vault else 0),
        })

    transactions = [{
        "id": str(tx.id),
        "stream_id": str(tx.stream_id) if tx.stream_id else None,
        "amount": _money(tx.amount),
        "type": tx.type,
        "narration": tx.narration,
        "category": tx.category,
        "source": tx.source,
        "reference": tx.squad_transaction_ref,
        "timestamp": _iso(tx.timestamp),
    } for tx in tx_result.scalars().all()]

    return {
        "id": str(user.id),
        "whatsapp_last4": _last4(user.whatsapp_no),
        "full_name": user.full_name,
        "location": user.location,
        "preferred_language": user.preferred_language,
        "onboarding_complete": bool(user.onboarding_complete),
        "verified_bank_name": user.verified_bank_name,
        "verified_bank_account_last4": _last4(user.verified_bank_account),
        "created_at": _iso(user.created_at),
        "streams": streams,
        "transactions": transactions,
        "score": None if not score else {
            "trader_score": float(score.trader_score or 0),
            "credit_grade": score.credit_grade,
            "consistency_score": float(score.consistency_score or 0),
            "volume_score": float(score.volume_score or 0),
            "savings_score": float(score.savings_score or 0),
            "tenure_score": float(score.tenure_score or 0),
            "recommended_loan_ceiling": _money(score.recommended_loan_ceiling),
            "computed_at": _iso(score.computed_at),
        },
    }


@router.get("/transactions", dependencies=[Depends(_require_admin)])
async def list_transactions(
    user: str | None = None,
    stream: str | None = None,
    type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    filters = []
    if user:
        filters.append(Transaction.user_id == user)
    if stream:
        filters.append(Transaction.stream_id == stream)
    if type:
        filters.append(Transaction.type == type)
    if date_from:
        filters.append(Transaction.timestamp >= date_from)
    if date_to:
        filters.append(Transaction.timestamp <= datetime.combine(date_to.date(), time.max, tzinfo=timezone.utc))

    where_clause = and_(*filters) if filters else True
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Transaction, User.full_name, IncomeStream.stream_name)
            .join(User, User.id == Transaction.user_id)
            .outerjoin(IncomeStream, IncomeStream.id == Transaction.stream_id)
            .where(where_clause)
            .order_by(desc(Transaction.timestamp))
            .limit(limit)
            .offset(offset)
        )
        total = await db.scalar(select(func.count()).select_from(Transaction).where(where_clause))

    transactions = []
    for tx, full_name, stream_name in result.all():
        transactions.append({
            "id": str(tx.id),
            "user_id": str(tx.user_id),
            "user_name": full_name,
            "stream_id": str(tx.stream_id) if tx.stream_id else None,
            "stream_name": stream_name,
            "amount": _money(tx.amount),
            "type": tx.type,
            "narration": tx.narration,
            "category": tx.category,
            "source": tx.source,
            "reference": tx.squad_transaction_ref,
            "timestamp": _iso(tx.timestamp),
        })
    return {"transactions": transactions, "total": int(total or 0)}


@router.get("/escalations", dependencies=[Depends(_require_admin)])
async def list_escalations():
    return {"escalations": []}
