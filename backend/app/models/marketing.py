import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class CampaignLink(Base):
    __tablename__ = "campaign_links"
    __table_args__ = (
        Index("idx_campaign_links_store_ref", "store_id", "ref_slug", unique=True),
        Index("idx_campaign_links_store_source", "store_id", "source"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    campaign_name = Column(String(150), nullable=False)
    source = Column(String(100), nullable=False)
    ref_slug = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CampaignVisit(Base):
    __tablename__ = "campaign_visits"
    __table_args__ = (
        Index("idx_campaign_visits_campaign_time", "campaign_id", "visited_at"),
        Index("idx_campaign_visits_session_once", "campaign_id", "session_id", unique=True, postgresql_where=text("session_id IS NOT NULL")),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaign_links.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(120))
    visited_at = Column(DateTime(timezone=True), server_default=func.now())


class CampaignEvent(Base):
    __tablename__ = "campaign_events"
    __table_args__ = (
        CheckConstraint("event_type IN ('product_view', 'add_to_cart')", name="ck_campaign_events_event_type"),
        Index("idx_campaign_events_campaign_type_time", "campaign_id", "event_type", "occurred_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaign_links.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))
    session_id = Column(String(120))
    event_type = Column(String(40), nullable=False)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())


class CampaignConversion(Base):
    __tablename__ = "campaign_conversions"
    __table_args__ = (
        Index("idx_campaign_conversions_order", "order_id", unique=True),
        Index("idx_campaign_conversions_campaign_time", "campaign_id", "converted_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaign_links.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    revenue = Column(Numeric(12, 2), nullable=False)
    converted_at = Column(DateTime(timezone=True), server_default=func.now())
