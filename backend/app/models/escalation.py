import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trigger_message = Column(Text, nullable=False)
    trigger_type = Column(String(30), nullable=False)  # "frustration", "explicit_request", "pin_lockout"
    conversation_snapshot = Column(JSON)
    status = Column(String(20), default="open")  # "open", "in_progress", "resolved"
    assigned_to = Column(String(100))
    resolution_note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
