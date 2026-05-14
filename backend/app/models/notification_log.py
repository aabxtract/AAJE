import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # "debrief", "reminder", "split_alert", "anomaly"
    message = Column(Text, nullable=False)
    channel = Column(String(20), default="whatsapp")
    status = Column(String(20), default="sent")  # "sent", "failed", "queued"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
