import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    price = Column(Numeric(12, 2), nullable=False, default=0)
    image_url = Column(String(1024))
    stock_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
