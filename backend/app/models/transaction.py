import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10))  # 'credit' | 'debit'
    category = Column(String(50))
    description = Column(String)
    source = Column(String(20))  # 'mono' | 'ocr' | 'manual'
    mono_transaction_id = Column(String(100), unique=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
