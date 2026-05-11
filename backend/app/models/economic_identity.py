import uuid
from sqlalchemy import Column, Float, Integer, String, Date, Numeric, JSON, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class EconomicIdentity(Base):
    __tablename__ = "economic_identities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    snapshot_date = Column(Date, nullable=False)
    trader_score = Column(Float)
    consistency_score = Column(Float)
    volume_score = Column(Float)
    savings_discipline_score = Column(Float)
    tenure_score = Column(Float)
    total_inflow_30d = Column(Numeric(14, 2))
    total_outflow_30d = Column(Numeric(14, 2))
    revenue_trend = Column(String(10))
    active_stream_count = Column(Integer)
    combined_credit_grade = Column(String(5))
    data_quality_score = Column(String(20)) # verified or standard
    recommended_loan_ceiling = Column(Numeric(14, 2))
    passport_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('user_id', 'snapshot_date', name='uq_economic_identities_user_date'),)
