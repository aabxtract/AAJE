import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)
    from_vault = Column(String(50))
    amount = Column(Numeric(12, 2), nullable=False)
    squad_transfer_ref = Column(String(100))
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
