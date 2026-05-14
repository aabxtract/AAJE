import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("type IN ('credit', 'debit')", name="transactions_type_check"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id"), nullable=True)
    order_id = Column(Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    stream_id = Column(Uuid(as_uuid=True), ForeignKey("income_streams.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10))
    narration = Column(Text)
    category = Column(String(50))
    source = Column(String(50))
    squad_transaction_ref = Column(String(100), unique=True)
    external_reference = Column(String(120))
    provider = Column(String(50))
    status = Column(String(30), default="completed")
    raw_payload = Column(Text)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
