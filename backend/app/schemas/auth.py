from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=7, max_length=20)


class GoogleSignupRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    google_id: Optional[str] = Field(default=None, max_length=255)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    auth_provider: str = "email"
    whatsapp_no: Optional[str] = None
    whatsapp_connected: bool = False
    whatsapp_verified: bool = False
    preferred_language: str = "en"
    onboarding_complete: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}

    # Legacy rows (pre-migration) may have NULL in columns that the current
    # schema declares non-nullable. Pydantic v2 does NOT fall back to the
    # field default when the value is present-but-None — it rejects. Coerce
    # None → default explicitly so /auth/login doesn't 500 for old users.
    @field_validator(
        "whatsapp_connected",
        "whatsapp_verified",
        "onboarding_complete",
        mode="before",
    )
    @classmethod
    def _coerce_none_bool(cls, v):
        return False if v is None else v

    @field_validator("preferred_language", mode="before")
    @classmethod
    def _coerce_none_language(cls, v):
        return "en" if v is None else v

    @field_validator("full_name", mode="before")
    @classmethod
    def _coerce_none_name(cls, v):
        return "" if v is None else v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ConnectWhatsappRequest(BaseModel):
    whatsapp_no: str = Field(min_length=10, max_length=20)

    @field_validator("whatsapp_no")
    @classmethod
    def normalize_number(cls, v: str) -> str:
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 10:
            raise ValueError("WhatsApp number must contain at least 10 digits")
        return digits


class VerifyWhatsappRequest(BaseModel):
    whatsapp_no: str = Field(min_length=10, max_length=20)
    otp: str = Field(min_length=6, max_length=6)

    @field_validator("whatsapp_no")
    @classmethod
    def normalize_number(cls, v: str) -> str:
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 10:
            raise ValueError("WhatsApp number must contain at least 10 digits")
        return digits

    @field_validator("otp")
    @classmethod
    def digits_only(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("OTP must be 6 digits")
        return v


class PayoutAccountRequest(BaseModel):
    """Manual-transfer payout account shown on the storefront checkout.

    Reuses ``users.verified_bank_*`` columns (originally Squad/Mono KYC). The
    storefront's PaymentAccount block reads these values directly. When
    Monnify + CAC re-enable, this same triple is used as the verified
    destination for automated payouts — no schema change needed.
    """

    account_number: str = Field(min_length=10, max_length=20)
    account_name: str = Field(min_length=1, max_length=100)
    bank_name: str = Field(min_length=1, max_length=100)
    bank_code: Optional[str] = Field(default=None, max_length=10)

    @field_validator("account_number")
    @classmethod
    def digits_only(cls, v: str) -> str:
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 10:
            raise ValueError("Account number must contain at least 10 digits")
        return digits


class PayoutAccountResponse(BaseModel):
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    bank_name: Optional[str] = None
    bank_code: Optional[str] = None
    ready: bool = False


class SetPinRequest(BaseModel):
    pin: str = Field(min_length=4, max_length=4)
    confirm_pin: str = Field(min_length=4, max_length=4)

    @field_validator("pin", "confirm_pin")
    @classmethod
    def digits_only(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN must be exactly 4 digits")
        return v
