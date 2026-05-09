import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    type = Column(String(30))
    delivered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    content_summary = Column(String)
