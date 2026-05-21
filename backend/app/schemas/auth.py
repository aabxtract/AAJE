from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    whatsapp_no: Optional[str] = None
    whatsapp_connected: bool = False
    whatsapp_verified: bool = False
    preferred_language: str = "en"
    onboarding_complete: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


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


class SetPinRequest(BaseModel):
    pin: str = Field(min_length=4, max_length=4)
    confirm_pin: str = Field(min_length=4, max_length=4)

    @field_validator("pin", "confirm_pin")
    @classmethod
    def digits_only(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN must be exactly 4 digits")
        return v
