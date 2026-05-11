import uuid
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class HustleStream(Base):
    __tablename__ = "hustle_streams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    stream_name = Column(String(100), nullable=False)
    stream_type = Column(String(50))
    squad_virtual_accounts = Column(JSON, default=dict)
    slice_config = Column(JSON, default=dict)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
