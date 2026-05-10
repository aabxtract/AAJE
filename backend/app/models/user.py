import uuid
from sqlalchemy import Column, String, Float, Boolean, DateTime, Time, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    whatsapp_no = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100))
    location = Column(String(100))
    business_type = Column(String(50))
    preferred_language = Column(String(10), default="en")
    pin_hash = Column(String(255))
    trader_score = Column(Float, default=0)
    mono_account_id = Column(String(100))
    verified_bank_account = Column(String(20))
    verified_bank_code = Column(String(10))
    verified_bank_name = Column(String(100))
    squad_customer_id = Column(String(100))
    squad_virtual_accounts = Column(JSON, default=dict)
    slice_config = Column(JSON, default=dict)
    daily_debrief_time = Column(Time)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_stage = Column(String(30), default="NEW")
    onboarding_complete = Column(Boolean, default=False)
    policies_accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
