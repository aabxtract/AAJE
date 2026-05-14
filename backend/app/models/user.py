import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True)
    password_hash = Column(String(255))
    full_name = Column(String(100))
    phone = Column(String(20))
    whatsapp_no = Column(String(20), unique=True, nullable=True)
    whatsapp_connected = Column(Boolean, default=False)
    location = Column(String(100))
    business_description = Column(Text)
    plan = Column(String(30), default="free")
    # WhatsApp / notification preferences
    whatsapp_daily_summary = Column(Boolean, default=True)
    whatsapp_order_notifications = Column(Boolean, default=True)
    preferred_language = Column(String(10), default="en")
    persona_mode = Column(String(40), default="normal_business_manager")
    pin_hash = Column(String(255))
    verified_bank_account = Column(String(20))
    verified_bank_code = Column(String(10))
    verified_bank_name = Column(String(100))
    squad_customer_id = Column(String(100))
    mono_account_id = Column(String(100))
    onboarding_complete = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
