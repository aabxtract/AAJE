import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    whatsapp_no = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100))
    location = Column(String(100))
    preferred_language = Column(String(10), default="en")
    pin_hash = Column(String(255))
    verified_bank_account = Column(String(20))
    verified_bank_code = Column(String(10))
    verified_bank_name = Column(String(100))
    squad_customer_id = Column(String(100))
    mono_account_id = Column(String(100))
    onboarding_complete = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
