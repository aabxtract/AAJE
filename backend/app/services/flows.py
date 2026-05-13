import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intelligence import FlowSession


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_flow_session(db: AsyncSession, user_id, flow_type: str, payload: dict | None = None) -> tuple[str, FlowSession]:
    token = secrets.token_urlsafe(32)
    session = FlowSession(
        token_hash=hash_token(token),
        user_id=user_id,
        flow_type=flow_type,
        payload_json=payload or {},
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        status="open",
    )
    db.add(session)
    await db.flush()
    return token, session


async def get_flow_session_by_token(db: AsyncSession, token: str) -> FlowSession | None:
    result = await db.execute(select(FlowSession).where(FlowSession.token_hash == hash_token(token)))
    session = result.scalar_one_or_none()
    if not session or session.status != "open":
        return None
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        session.status = "expired"
        return None
    return session
