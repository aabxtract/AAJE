import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    from_vault = Column(String(50))
    amount = Column(Numeric(12, 2), nullable=False)
    destination_account = Column(String(20))
    squad_transfer_ref = Column(String(100))
    status = Column(String(20), default="pending")
    initiated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
