"""LLM-driven onboarding turn endpoint.

POST /onboarding/turn
  Body: { history: [{role, content}, ...] }
  Auth: JWT required
  Returns: { message, quick_replies?, placeholder?, done, store? }

The LLM decides what to ask, when to suggest templates, and when to call
finalize_onboarding. There are no scripted questions — the only structure
is the system prompt + two tools (see app/intelligence/onboarding.py).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.intelligence.onboarding import run_onboarding_turn
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class HistoryEntry(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=2000)


class OnboardingTurnRequest(BaseModel):
    history: list[HistoryEntry] = Field(default_factory=list, max_length=40)


class OnboardingTurnResponse(BaseModel):
    message: str
    quick_replies: Optional[list[str]] = None
    placeholder: Optional[str] = None
    done: bool = False
    store: Optional[dict] = None


@router.post("/turn", response_model=OnboardingTurnResponse)
async def turn(
    body: OnboardingTurnRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingTurnResponse:
    result = await run_onboarding_turn(
        [h.model_dump() for h in body.history],
        db=db,
        user=user,
    )
    return OnboardingTurnResponse(**result)
