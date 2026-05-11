import uuid
from sqlalchemy import Column, String, Float, Boolean, DateTime, Time, JSON, Numeric
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
    # Module/Tier fields
    tier = Column(String(20), default="module_2") # module_1 or module_2
    subscription_status = Column(String(20), default="inactive") # active, suspended, cancelled
    subscription_start_date = Column(DateTime(timezone=True))
    last_payment_date = Column(DateTime(timezone=True))
    next_payment_date = Column(DateTime(timezone=True))
    subscription_amount = Column(Numeric(10, 2), default=1000.00)
    migration_eligible = Column(Boolean, default=False)
    
    daily_debrief_time = Column(Time)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_stage = Column(String(30), default="NEW")
    onboarding_complete = Column(Boolean, default=False)
    policies_accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
