import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"))
    business_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"))
    type = Column(String(50))
    channel = Column(String(40), default="dashboard")
    message = Column(Text)
    content = Column(Text)
    delivered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
