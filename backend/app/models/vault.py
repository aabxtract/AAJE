import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class Vault(Base):
    __tablename__ = "vaults"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stream_id = Column(UUID(as_uuid=True), ForeignKey("income_streams.id"), unique=True)
    current_balance = Column(Numeric(12, 2), default=0)
    total_deposited = Column(Numeric(12, 2), default=0)
    total_withdrawn = Column(Numeric(12, 2), default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
