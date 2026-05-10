import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10))
    category = Column(String(50))
    description = Column(String(500))
    source = Column(String(20))
    mono_transaction_id = Column(String(100), unique=True, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
