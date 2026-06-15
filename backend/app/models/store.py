import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.sql import func

from app.database import Base

_JSON = JSON().with_variant(JSONB, "postgresql")


class Store(Base):
    __tablename__ = "stores"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    store_name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    store_slug = Column(String(100), unique=True, nullable=False)
    business_type = Column(String(40), default="physical_products")
    instagram_handle = Column(String(120))
    description = Column(Text)
    store_description = Column(Text)
    whatsapp_number = Column(String(20))
    theme_config = Column(_JSON, default=dict)
    theme_json = Column(_JSON, default=dict)
    theme = Column(String(50), default="default")
    config_json = Column(_JSON, default=dict)
    template = Column(String(50), default="fashion")
    logo_url = Column(Text)
    banner_url = Column(Text)
    contact_whatsapp = Column(String(20))
    tagline = Column(String(255))
    squad_virtual_account_id = Column(String(100))
    squad_virtual_account_number = Column(String(20))
    squad_customer_identifier = Column(String(120), unique=True)
    has_squad_account = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
