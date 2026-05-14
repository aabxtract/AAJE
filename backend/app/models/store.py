import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_name = Column(String(150), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    logo_url = Column(String(1024))
    theme_json = Column(JSON)
    contact_whatsapp = Column(String(40))
    business_category = Column(String(120))
    pickup_delivery_note = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
