import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    trader_score = Column(Float, default=0)
    data_quality = Column(String(30), default="low")
    credit_grade = Column(String(5))
    consistency_score = Column(Float, default=0)
    volume_score = Column(Float, default=0)
    savings_score = Column(Float, default=0)
    tenure_score = Column(Float, default=0)
    recommended_loan_ceiling = Column(Numeric(14, 2))
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
