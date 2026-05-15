import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.commerce import Store
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str
    phone: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ConnectWhatsappRequest(BaseModel):
    whatsapp_no: str


@router.post("/signup")
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Create user account only. Store is created later during onboarding confirm."""
    if not payload.phone:
        raise HTTPException(status_code=400, detail="Phone number required")

    whatsapp_no = _normalize_whatsapp_number(payload.phone)
    existing = (await db.execute(select(User).where(User.email == payload.email.lower()))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")
    existing_whatsapp = (await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))).scalar_one_or_none()
    if existing_whatsapp:
        raise HTTPException(status_code=409, detail="WhatsApp number already exists")

    user = User(
        email=payload.email.lower(),
        password_hash=_hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        whatsapp_no=whatsapp_no,
        whatsapp_connected=True,
        onboarding_complete=False,
        persona_mode="storefront_operations_free",
    )
    db.add(user)
    await db.flush()
    return {
        "token": _create_token(str(user.id)),
        "user": _user_payload(user),
    }


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == payload.email.lower()))).scalar_one_or_none()
    if not user or not _verify_password(payload.password, user.password_hash or ""):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": _create_token(str(user.id)), "user": _user_payload(user)}


@router.get("/me")
async def me(authorization: str | None = Header(default=None), db: AsyncSession = Depends(get_db)):
    user = await _current_user(db, authorization)
    return _user_payload(user)


@router.post("/connect-whatsapp")
async def connect_whatsapp(payload: ConnectWhatsappRequest, authorization: str | None = Header(default=None), db: AsyncSession = Depends(get_db)):
    user = await _current_user(db, authorization)
    whatsapp_no = _normalize_whatsapp_number(payload.whatsapp_no)
    user.whatsapp_no = whatsapp_no
    user.whatsapp_connected = True
    user.persona_mode = "storefront_operations_free" if user.plan == "free" else "storefront_operations_premium"
    stores = (await db.execute(select(Store).where(Store.user_id == user.id))).scalars().all()
    for store in stores:
        store.contact_whatsapp = whatsapp_no
        store.whatsapp_number = whatsapp_no
    return {"status": "connected", "user": _user_payload(user)}


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    whatsapp_no: str | None = None
    verified_bank_account: str | None = None
    verified_bank_code: str | None = None
    verified_bank_name: str | None = None


@router.post("/update-me")
async def update_me(payload: UpdateUserRequest, authorization: str | None = Header(default=None), db: AsyncSession = Depends(get_db)):
    user = await _current_user(db, authorization)
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.whatsapp_no is not None:
        user.whatsapp_no = _normalize_whatsapp_number(payload.whatsapp_no)
    if payload.verified_bank_account is not None:
        user.verified_bank_account = payload.verified_bank_account
    if payload.verified_bank_code is not None:
        user.verified_bank_code = payload.verified_bank_code
    if payload.verified_bank_name is not None:
        user.verified_bank_name = payload.verified_bank_name
    
    await db.flush()
    return {"status": "updated", "user": _user_payload(user)}


async def _current_user(db: AsyncSession, authorization: str | None) -> User:
    user_id = _decode_authorization(authorization)
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _create_token(user_id: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)).timestamp()),
    }
    signing_input = f"{_b64(header)}.{_b64(payload)}"
    secret = settings.jwt_secret or settings.secret_key
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64_bytes(signature)}"


def _decode_authorization(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        secret = settings.jwt_secret or settings.secret_key
        expected = _b64_bytes(hmac.new(secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest())
        if not hmac.compare_digest(expected, signature_b64):
            raise ValueError("bad signature")
        payload = json.loads(_b64_decode(payload_b64))
        if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("expired")
        return payload["sub"]
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def _b64(data: dict) -> str:
    return _b64_bytes(json.dumps(data, separators=(",", ":")).encode("utf-8"))


def _b64_bytes(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_decode(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")


def _normalize_whatsapp_number(value: str | None) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if digits.startswith("0") and len(digits) == 11:
        return f"234{digits[1:]}"
    return digits


def _user_payload(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "plan": getattr(user, "plan", "free"),
        "full_name": user.full_name,
        "phone": user.phone,
        "whatsapp_no": user.whatsapp_no,
        "whatsapp_connected": user.whatsapp_connected,
        "preferred_language": user.preferred_language,
        "business_description": user.business_description,
        "persona_mode": user.persona_mode,
        "onboarding_complete": user.onboarding_complete,
    }
