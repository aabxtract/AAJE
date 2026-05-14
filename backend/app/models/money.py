import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class VirtualAccount(Base):
    __tablename__ = "virtual_accounts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_name = Column(String(100))
    account_number = Column(String(20), unique=True)
    squad_account_id = Column(String(100))
    bank_name = Column(String(100), default="GTBank")
    is_primary = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    available_balance = Column(Numeric(12, 2), default=0)
    total_earned = Column(Numeric(12, 2), default=0)
    total_withdrawn = Column(Numeric(12, 2), default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    alias = Column(String(100))
    bank_name = Column(String(100))
    bank_code = Column(String(10))
    account_number = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MonoTransaction(Base):
    __tablename__ = "mono_transactions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2))
    type = Column(String(10))
    narration = Column(Text)
    date = Column(DateTime(timezone=True))
    mono_id = Column(String(100), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FailedTransfer(Base):
    __tablename__ = "failed_transfers"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    destination_json = Column(Text)
    reference = Column(String(120), unique=True)
    error_message = Column(Text)
    retry_count = Column(Numeric(3, 0), default=0)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
