import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    alias = Column(String(100), nullable=False)
    bank_name = Column(String(100))
    bank_code = Column(String(10))
    account_number = Column(String(20))
    account_name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
