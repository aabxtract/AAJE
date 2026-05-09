import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    raw_image_url = Column(String)
    extracted_data = Column(JSON)
    linked_transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
