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
from app.models.user import User
from app.storefront.service import create_storefront_from_description

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str
    business_description: str
    phone: str | None = None
    create_squad_account: bool = True


class GoogleSignupRequest(BaseModel):
    email: str
    full_name: str | None = None
    phone: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ConnectWhatsappRequest(BaseModel):
    whatsapp_no: str


@router.post("/signup")
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    # For email-based signup, require phone collection per spec
    if not payload.phone:
        raise HTTPException(status_code=400, detail="Phone number required for email signups")

    existing = (await db.execute(select(User).where(User.email == payload.email.lower()))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")
    user = User(
        email=payload.email.lower(),
        password_hash=_hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        business_description=payload.business_description,
        onboarding_complete=True,
        persona_mode="storefront_extension",
    )
    db.add(user)
    await db.flush()
    store = await create_storefront_from_description(db, user, payload.business_description, payload.create_squad_account)
    return {
        "token": _create_token(str(user.id)),
        "user": _user_payload(user),
        "store": {
            "id": str(store.id),
            "slug": store.slug,
            "store_slug": store.store_slug,
            "store_name": store.store_name,
            "link": f"/{store.slug}",
            "has_squad_account": store.has_squad_account,
            "squad_virtual_account_number": store.squad_virtual_account_number,
        },
    }


@router.post("/google-signin")
async def google_signin(payload: GoogleSignupRequest, db: AsyncSession = Depends(get_db)):
    # Placeholder/mock google auth: accept email and optionally create user
    existing = (await db.execute(select(User).where(User.email == payload.email.lower()))).scalar_one_or_none()
    if existing:
        return {"token": _create_token(str(existing.id)), "user": _user_payload(existing)}

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name or "",
        phone=payload.phone,
        onboarding_complete=True,
        persona_mode="storefront_extension",
        plan="free",
    )
    db.add(user)
    await db.flush()
    # Do not create storefront automatically for google mock; let client call AI create flow
    return {"token": _create_token(str(user.id)), "user": _user_payload(user)}


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
    user.whatsapp_no = payload.whatsapp_no
    user.whatsapp_connected = True
    user.persona_mode = "storefront_extension"
    return {"status": "connected", "user": _user_payload(user)}


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
    }
