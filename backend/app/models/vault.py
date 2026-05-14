import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Vault(Base):
    __tablename__ = "vaults"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id"), nullable=True)
    stream_id = Column(Uuid(as_uuid=True), ForeignKey("income_streams.id"), unique=True)
    name = Column(String(120), default="Main Vault")
    current_balance = Column(Numeric(12, 2), default=0)
    percentage = Column(Numeric(5, 2), default=0)
    is_default = Column(Boolean, default=False)
    total_deposited = Column(Numeric(12, 2), default=0)
    total_withdrawn = Column(Numeric(12, 2), default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
