"""
Admin dashboard API endpoints.
All routes require a valid bearer token matching ADMIN_TOKEN in .env.
"""
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

router = APIRouter()
_bearer = HTTPBearer()


def _require_admin(credentials: HTTPAuthorizationCredentials = Security(_bearer)):
    if credentials.credentials != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return True


@router.get("/stats", dependencies=[Depends(_require_admin)])
async def get_stats():
    """High-level platform stats for dashboard home."""
    # TODO: query Postgres for live counts
    return {
        "total_traders": 0,
        "active_today": 0,
        "transactions_today": 0,
        "total_vault_balance": 0,
    }


@router.get("/users", dependencies=[Depends(_require_admin)])
async def list_users(limit: int = 50, offset: int = 0):
    """Paginated trader list."""
    # TODO: implement
    return {"users": [], "total": 0}


@router.get("/transactions", dependencies=[Depends(_require_admin)])
async def list_transactions(limit: int = 50, offset: int = 0):
    """Paginated transaction list."""
    # TODO: implement
    return {"transactions": [], "total": 0}


@router.get("/escalations", dependencies=[Depends(_require_admin)])
async def list_escalations():
    """Open escalations for human review."""
    # TODO: implement
    return {"escalations": []}
