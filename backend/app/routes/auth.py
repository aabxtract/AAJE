from __future__ import annotations

import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.wallet import Wallet
from app.redis import clear_whatsapp_otp, get_whatsapp_otp, set_whatsapp_otp
from app.schemas.auth import (
    ConnectWhatsappRequest,
    LoginRequest,
    SetPinRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
    VerifyWhatsappRequest,
)
from app.services.auth_service import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.services.pin import hash_pin, is_valid_pin
from app.services.whatsapp_client import send_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()
    db.add(Wallet(user_id=user.id))
    await db.commit()
    await db.refresh(user)

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/connect-whatsapp")
async def connect_whatsapp(
    body: ConnectWhatsappRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    other = await db.execute(
        select(User).where(User.whatsapp_no == body.whatsapp_no, User.id != user.id)
    )
    if other.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409, detail="WhatsApp number already linked to another account"
        )

    otp = f"{secrets.randbelow(1_000_000):06d}"
    await set_whatsapp_otp(str(user.id), body.whatsapp_no, otp)

    try:
        await send_text(
            body.whatsapp_no,
            f"Your AAJE verification code is {otp}\n\nThis code expires in 10 minutes. "
            "Do not share it with anyone.",
        )
    except Exception:
        logger.exception("Failed to send WhatsApp OTP")
        raise HTTPException(status_code=502, detail="Could not send verification code")

    return {"ok": True, "message": "Verification code sent via WhatsApp"}


@router.post("/verify-whatsapp", response_model=UserResponse)
async def verify_whatsapp(
    body: VerifyWhatsappRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    stored = await get_whatsapp_otp(str(user.id), body.whatsapp_no)
    if not stored or not secrets.compare_digest(stored, body.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    await clear_whatsapp_otp(str(user.id), body.whatsapp_no)

    user.whatsapp_no = body.whatsapp_no
    user.whatsapp_connected = True
    user.whatsapp_verified = True
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.patch("/set-pin")
async def set_pin(
    body: SetPinRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if body.pin != body.confirm_pin:
        raise HTTPException(status_code=400, detail="PINs do not match")

    if not is_valid_pin(body.pin):
        raise HTTPException(
            status_code=400,
            detail="PIN must be exactly 4 digits and not an obvious pattern (e.g. 1234, 0000)",
        )

    user.pin_hash = hash_pin(body.pin)
    await db.commit()
    return {"ok": True, "message": "PIN set successfully"}
