import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
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
    email_clean = payload.email.strip().lower()
    existing = (await db.execute(select(User).where(User.email == email_clean))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")
    existing_whatsapp = (await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))).scalar_one_or_none()
    if existing_whatsapp:
        raise HTTPException(status_code=409, detail="WhatsApp number already exists")

    user = User(
        email=email_clean,
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
    email_clean = payload.email.strip().lower()
    user = (await db.execute(select(User).where(User.email == email_clean))).scalar_one_or_none()
    if not user or not _verify_password(payload.password, user.password_hash or ""):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": _create_token(str(user.id)), "user": _user_payload(user)}


class WhatsappLoginRequest(BaseModel):
    whatsapp_no: str


@router.post("/whatsapp-login")
async def whatsapp_login(payload: WhatsappLoginRequest, db: AsyncSession = Depends(get_db)):
    whatsapp_no = _normalize_whatsapp_number(payload.whatsapp_no)
    user = (await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Connect your AAJE account to use AAJE on WhatsApp.",
        )

    return {
        "token": _create_token(str(user.id)),
        "user": _user_payload(user),
        "is_new": False,
    }


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


@router.post("/verify-whatsapp-connection")
async def verify_whatsapp_connection(authorization: str | None = Header(default=None), db: AsyncSession = Depends(get_db)):
    user = await _current_user(db, authorization)
    if not user.whatsapp_no:
        raise HTTPException(status_code=400, detail="WhatsApp number not set")
    
    from app.whatsapp.service import send_text
    
    store = (await db.execute(select(Store).where(Store.user_id == user.id))).scalar_one_or_none()
    store_name = store.store_name if store else "your AAJE storefront"
    
    message = (
        f"✅ Connection successful!\n\n"
        f"AAJE is now connected to {store_name}.\n"
        f"You will receive notifications here for new orders and payments.\n\n"
        f"Reply 'help' anytime to see what I can do for you."
    )
    
    try:
        await send_text(user.whatsapp_no, message)
    except Exception as e:
        # In non-prod without creds, this might "fail" but we want to know
        return {"status": "error", "detail": str(e)}

    return {"status": "message_sent"}


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
        "mono_account_id": user.mono_account_id,
        "verified_bank_account": user.verified_bank_account,
        "verified_bank_code": user.verified_bank_code,
        "verified_bank_name": user.verified_bank_name,
    }


@router.get("/flow/dummy")
async def dummy_flow(wa: str):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>AAJE Account Link</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 400px; margin: 0 auto; background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h2 {{ margin-top: 0; color: #111b21; }}
            input {{ width: 100%; padding: 12px; margin-bottom: 16px; border: 1px solid #d1d7db; border-radius: 8px; box-sizing: border-box; font-size: 16px; }}
            button {{ width: 100%; padding: 14px; background: #00a884; color: white; border: none; border-radius: 24px; font-weight: bold; font-size: 16px; cursor: pointer; }}
            .whatsapp-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 20px; color: #00a884; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="whatsapp-header">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766.001-3.187-2.575-5.77-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.299.045-.677.063-1.092-.069-.252-.08-.575-.187-.988-.365-1.739-.751-2.874-2.502-2.961-2.617-.087-.116-.708-.94-.708-1.793s.448-1.273.607-1.446c.159-.173.346-.217.462-.217l.332.006c.106.005.249-.04.39.298.144.347.491 1.2.534 1.287.043.087.072.188.014.304-.058.116-.087.188-.173.289l-.26.304c-.087.086-.177.18-.076.354.101.174.449.741.964 1.201.662.591 1.221.774 1.394.86s.274.072.376-.043c.101-.116.433-.506.549-.68.116-.173.231-.145.39-.087s1.011.477 1.184.564.289.13.332.202c.045.072.045.419-.101.824z"/></svg>
                AAJE Account Link
            </div>
            <h2>Connect AAJE</h2>
            <p style="color: #667781; font-size: 14px; margin-bottom: 24px;">Sign in or create an account to connect AAJE to this WhatsApp number.</p>
            
            <form action="/auth/flow/submit" method="POST">
                <input type="hidden" name="wa" value="{wa}">
                
                <label style="display:block; margin-bottom:8px; font-weight:bold; font-size:14px; color:#111b21;">WhatsApp Number</label>
                <input type="text" value="{wa}" disabled style="background: #e9edef; color: #667781;">
                
                <label style="display:block; margin-bottom:8px; font-weight:bold; font-size:14px; color:#111b21;">Email</label>
                <input type="email" name="email" placeholder="store@example.com" required>
                
                <label style="display:block; margin-bottom:8px; font-weight:bold; font-size:14px; color:#111b21;">Secure Password</label>
                <input type="password" name="password" placeholder="••••••••" required minlength="6">
                
                <button type="submit">Connect Account</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.post("/flow/submit")
async def flow_submit(wa: str = Form(...), email: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    whatsapp_no = _normalize_whatsapp_number(wa)
    
    email_clean = email.strip().lower()
    user = (await db.execute(select(User).where(User.email == email_clean))).scalar_one_or_none()
    
    from app.models.commerce import Store
    store = None
    
    if user:
        # Existing user - verify password
        if not _verify_password(password, user.password_hash or ""):
            html_error = """
            <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Error</title></head>
            <body style="font-family:sans-serif; text-align:center; padding:50px;">
                <h2 style="color:#d9534f;">Invalid Credentials</h2>
                <p>The password you entered is incorrect for this email.</p>
                <a href="javascript:history.back()" style="color:#00a884; text-decoration:none; font-weight:bold;">Go Back</a>
            </body></html>
            """
            return HTMLResponse(content=html_error, status_code=400)
            
        # Link WhatsApp to existing user
        user.whatsapp_no = whatsapp_no
        user.phone = user.phone or wa
        user.whatsapp_connected = True
        
        # Link store if they have one
        store = (await db.execute(select(Store).where(Store.user_id == user.id))).scalar_one_or_none()
        if store:
            store.contact_whatsapp = whatsapp_no
            store.whatsapp_number = whatsapp_no
    else:
        # Create a new user
        user = User(
            email=email_clean,
            password_hash=_hash_password(password),
            whatsapp_no=whatsapp_no,
            phone=wa,
            whatsapp_connected=True,
            onboarding_complete=False,
            persona_mode="storefront_operations_free",
        )
        db.add(user)
        
    await db.commit()
    
    # Notify user in WhatsApp
    from app.whatsapp.service import send_text
    try:
        if store:
            await send_text(whatsapp_no, f"Account linked successfully. AAJE is now connected to {store.store_name}.\n\nReply help anytime.")
        else:
            await send_text(whatsapp_no, "AAJE account connected. Create or publish your storefront from the web dashboard, then return here to manage it on WhatsApp.")
    except Exception:
        pass
        
    # Redirect back to WhatsApp bot via intent
    from app.config import settings
    bot_number = settings.whatsapp_bot_number or "2348000000000"
    bot_number = bot_number.replace("+", "")
    
    redirect_url = f"https://wa.me/{bot_number}?text=Connected"
    
    success_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>AAJE Connected</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh; text-align: center; }}
            h2 {{ color: #111b21; }}
            p {{ color: #667781; margin-bottom: 30px; }}
            a.button {{ display: inline-block; padding: 14px 30px; background: #00a884; color: white; border-radius: 24px; font-weight: bold; font-size: 16px; text-decoration: none; }}
        </style>
        <script>
            setTimeout(function() {{
                window.location.href = "{redirect_url}";
            }}, 1000);
        </script>
    </head>
    <body>
        <svg viewBox="0 0 24 24" width="60" height="60" fill="#00a884" style="margin-bottom: 20px;"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
        <h2>AAJE Account Connected</h2>
        <p>Your account is now linked. You will be redirected back to WhatsApp automatically.</p>
        <a href="{redirect_url}" class="button">Return to WhatsApp</a>
    </body>
    </html>
    """
    
    return HTMLResponse(content=success_html)
