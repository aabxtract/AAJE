import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    raw_image_url = Column(String(500))
    extracted_data = Column(JSON)
    linked_transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
