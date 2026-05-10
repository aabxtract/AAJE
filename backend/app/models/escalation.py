import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    trigger_message = Column(String(500))
    trigger_type = Column(String(30))
    conversation_snapshot = Column(JSON)
    status = Column(String(20), default="open")
    admin_notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
