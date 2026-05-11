import uuid
from sqlalchemy import Column, Integer, Date, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class StreamAnalytics(Base):
    __tablename__ = "stream_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    stream_id = Column(UUID(as_uuid=True), ForeignKey("hustle_streams.id"))
    analytics_date = Column(Date, nullable=False)
    total_inflow = Column(Numeric(12, 2), default=0)
    total_outflow = Column(Numeric(12, 2), default=0)
    transaction_count = Column(Integer, default=0)
    vault_split_count = Column(Integer, default=0)
    fees_collected = Column(Numeric(8, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('stream_id', 'analytics_date', name='uq_stream_analytics_stream_date'),)
