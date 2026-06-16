import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    available_balance = Column(Numeric(12, 2), default=0)
    total_earned = Column(Numeric(12, 2), default=0)
    total_orders_paid = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
