import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class NudgeLog(Base):
    __tablename__ = "nudge_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    trigger_volume_30d = Column(Numeric(14, 2))
    trigger_subscription_paid = Column(Numeric(14, 2))
    projected_interest = Column(Numeric(14, 2))
    responded = Column(Boolean, default=False)
    response_action = Column(String(50)) # upgrade_clicked, ignored
