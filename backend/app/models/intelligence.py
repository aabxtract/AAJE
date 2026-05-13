import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(80), nullable=False)
    source = Column(String(60), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=True)
    payload_json = Column(JSONB, default=dict)
    processed = Column(Boolean, default=False)
    idempotency_key = Column(String(160), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=True)
    vault_id = Column(UUID(as_uuid=True), ForeignKey("vaults.id"), nullable=True)
    direction = Column(String(10), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(5), default="NGN")
    reference = Column(String(120), nullable=False)
    source = Column(String(60), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FlowSession(Base):
    __tablename__ = "flow_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(128), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    flow_type = Column(String(80), nullable=False)
    payload_json = Column(JSONB, default=dict)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(30), default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Consent(Base):
    __tablename__ = "consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    consent_type = Column(String(80), nullable=False)
    institution_id = Column(String(120))
    token_hash = Column(String(128), unique=True)
    scopes = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ScoreEvent(Base):
    __tablename__ = "score_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score = Column(Numeric(8, 2), nullable=False)
    grade = Column(String(5))
    factors_json = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BizPrintSnapshot(Base):
    __tablename__ = "bizprint_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=True)
    data_quality = Column(String(30), default="low")
    snapshot_json = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor = Column(String(120), nullable=False)
    action = Column(String(120), nullable=False)
    target_type = Column(String(80))
    target_id = Column(String(120))
    metadata_json = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
