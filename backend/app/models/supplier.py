import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    alias = Column(String(50))
    bank_name = Column(String(100))
    bank_code = Column(String(10))
    account_number = Column(String(20))
    phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
