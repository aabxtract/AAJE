import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    fee = Column(Numeric(8, 2), default=0)
    net_amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(20))
    narration = Column(Text)
    monnify_ref = Column(String(100))
    status = Column(String(20), default="success")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
