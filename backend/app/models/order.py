import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id"))
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"))
    order_ref = Column(String(20), unique=True, nullable=True)
    customer_name = Column(String(200))
    customer_phone = Column(String(40))
    customer_whatsapp = Column(String(20))
    customer_email = Column(String(255))
    total_amount = Column(Numeric(12, 2), nullable=True)
    status = Column(String(20), default="pending")
    payment_status = Column(String(30), default="pending")
    order_status = Column(String(30), default="pending")
    monnify_payment_ref = Column(String(100))
    monnify_transaction_ref = Column(String(100))
    squad_payment_reference = Column(String(200), unique=True)
    squad_transaction_ref = Column(String(100))
    payment_method = Column(String(20), default="transfer")
    payment_link = Column(Text)
    notes = Column(Text)
    delivery_address = Column(Text)
    campaign_ref = Column(String(100))
    idempotency_key = Column(String(120), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True))
