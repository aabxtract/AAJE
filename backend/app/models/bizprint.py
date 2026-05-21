import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.sql import func

from app.database import Base


class BizPrint(Base):
    __tablename__ = "bizprints"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trader_score = Column(Float, default=0)
    credit_grade = Column(String(5))
    consistency_score = Column(Float, default=0)
    volume_score = Column(Float, default=0)
    growth_score = Column(Float, default=0)
    tenure_score = Column(Float, default=0)
    recommended_loan_ceiling = Column(Numeric(14, 2), default=0)
    total_orders_analyzed = Column(Integer, default=0)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
