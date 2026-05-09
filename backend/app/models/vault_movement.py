import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class VaultMovement(Base):
    __tablename__ = "vault_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    source_transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    vault_name = Column(String(50))
    amount = Column(Numeric(12, 2), nullable=False)
    direction = Column(String(10))  # 'in' | 'out'
    squad_transfer_ref = Column(String(100))
    fee_charged = Column(Numeric(6, 2), default=5.00)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
