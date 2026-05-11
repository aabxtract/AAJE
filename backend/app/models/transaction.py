import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("type IN ('credit', 'debit')", name="transactions_type_check"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stream_id = Column(UUID(as_uuid=True), ForeignKey("income_streams.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10))
    narration = Column(Text)
    category = Column(String(50))
    source = Column(String(50))
    squad_transaction_ref = Column(String(100), unique=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
