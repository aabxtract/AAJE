import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id"))
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"))
    order_ref = Column(String(20), unique=True, nullable=False)
    customer_name = Column(String(100))
    customer_whatsapp = Column(String(20))
    customer_email = Column(String(255))
    total_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default="pending")
    payment_status = Column(String(20), default="unpaid")
    monnify_payment_ref = Column(String(100))
    monnify_transaction_ref = Column(String(100))
    payment_link = Column(Text)
    notes = Column(Text)
    delivery_address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
