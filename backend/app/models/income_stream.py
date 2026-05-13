import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class IncomeStream(Base):
    __tablename__ = "income_streams"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("public.users.id", ondelete="CASCADE"), nullable=False)
    stream_name = Column(String(100), nullable=False)
    stream_type = Column(String(50))
    squad_account_id = Column(String(100))
    squad_account_number = Column(String(20))
    split_percentage = Column(Numeric(5, 2))
    is_savings = Column(Boolean, default=False)
    is_emergency = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
