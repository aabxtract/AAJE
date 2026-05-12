"""
Admin dashboard API endpoints.
All routes require a valid bearer token matching ADMIN_TOKEN in .env.

Provides:
  - Platform stats (total traders, today's activity, vault totals)
  - Paginated user listing with score data
  - Paginated transaction listing
  - Open escalation management (list + resolve)
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.escalation import Escalation
from app.models.score import Score
from app.models.transaction import Transaction
from app.models.user import User
from app.models.vault import Vault
from app.redis import clear_session, save_session
from app.services.whatsapp_client import send_text

router = APIRouter()
_bearer = HTTPBearer()


def _require_admin(credentials: HTTPAuthorizationCredentials = Security(_bearer)):
    if credentials.credentials != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return True


@router.get("/stats", dependencies=[Depends(_require_admin)])
async def get_stats():
    """High-level platform stats for dashboard home."""
    async with AsyncSessionLocal() as db:
        total_traders = await db.scalar(
            select(func.count()).select_from(User).where(User.onboarding_complete == True)
        )

        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        transactions_today = await db.scalar(
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.timestamp >= today_start)
        )
        volume_today = await db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.timestamp >= today_start)
            .where(Transaction.type == "credit")
        )
        total_vault_balance = await db.scalar(
            select(func.coalesce(func.sum(Vault.current_balance), 0))
        )
        open_escalations = await db.scalar(
            select(func.count())
            .select_from(Escalation)
            .where(Escalation.status == "open")
        )

    return {
        "total_traders": total_traders or 0,
        "transactions_today": transactions_today or 0,
        "volume_today": float(volume_today or 0),
        "total_vault_balance": float(total_vault_balance or 0),
        "open_escalations": open_escalations or 0,
    }


@router.get("/users", dependencies=[Depends(_require_admin)])
async def list_users(limit: int = 50, offset: int = 0):
    """Paginated trader list with score data."""
    async with AsyncSessionLocal() as db:
        total = await db.scalar(
            select(func.count()).select_from(User).where(User.onboarding_complete == True)
        )
        result = await db.execute(
            select(User, Score)
            .outerjoin(Score, Score.user_id == User.id)
            .where(User.onboarding_complete == True)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = result.all()

    users = []
    for user, score in rows:
        users.append({
            "id": str(user.id),
            "whatsapp_no": user.whatsapp_no,
            "full_name": user.full_name,
            "location": user.location,
            "language": user.preferred_language,
            "trader_score": score.trader_score if score else 0,
            "credit_grade": score.credit_grade if score else "D",
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })

    return {"users": users, "total": total or 0}


@router.get("/transactions", dependencies=[Depends(_require_admin)])
async def list_transactions(limit: int = 50, offset: int = 0):
    """Paginated transaction list."""
    async with AsyncSessionLocal() as db:
        total = await db.scalar(select(func.count()).select_from(Transaction))
        result = await db.execute(
            select(Transaction)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        transactions = result.scalars().all()

    tx_list = [
        {
            "id": str(tx.id),
            "user_id": str(tx.user_id),
            "amount": float(tx.amount),
            "type": tx.type,
            "category": tx.category,
            "narration": tx.narration,
            "source": tx.source,
            "reference": tx.squad_transaction_ref,
            "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
        }
        for tx in transactions
    ]
    return {"transactions": tx_list, "total": total or 0}


@router.get("/escalations", dependencies=[Depends(_require_admin)])
async def list_escalations():
    """Open escalations for human review."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Escalation, User)
            .join(User, User.id == Escalation.user_id)
            .where(Escalation.status.in_(["open", "in_progress"]))
            .order_by(Escalation.created_at.desc())
        )
        rows = result.all()

    escalations = []
    for esc, user in rows:
        escalations.append({
            "id": str(esc.id),
            "user_id": str(esc.user_id),
            "trader_name": user.full_name,
            "whatsapp_no": user.whatsapp_no,
            "trigger_type": esc.trigger_type,
            "trigger_message": esc.trigger_message,
            "status": esc.status,
            "created_at": esc.created_at.isoformat() if esc.created_at else None,
        })

    return {"escalations": escalations}


@router.post("/escalations/{escalation_id}/resolve", dependencies=[Depends(_require_admin)])
async def resolve_escalation(escalation_id: str, reply: str = "", note: str = ""):
    """Resolve an escalation — optionally send a reply to the trader and unfreeze their session."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Escalation).where(Escalation.id == escalation_id)
        )
        escalation = result.scalar_one_or_none()
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")

        user = await db.get(User, escalation.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        escalation.status = "resolved"
        escalation.resolution_note = note or "Resolved by admin"
        escalation.resolved_at = datetime.now(timezone.utc)
        await db.commit()

    # Unfreeze the trader's session
    await clear_session(user.whatsapp_no)

    # Send reply to the trader if provided
    if reply:
        await send_text(user.whatsapp_no, reply)
    else:
        await send_text(
            user.whatsapp_no,
            "Your issue has been resolved. You can continue using AAJE normally. 🙏",
        )

    return {"status": "resolved", "escalation_id": escalation_id}
