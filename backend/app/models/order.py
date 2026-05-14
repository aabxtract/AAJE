import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    customer_name = Column(String(200))
    customer_phone = Column(String(40))
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    payment_status = Column(String(30), default="pending")
    order_status = Column(String(30), default="pending")
    squad_payment_reference = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
