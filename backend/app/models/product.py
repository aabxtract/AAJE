import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Numeric(12, 2), nullable=False)
    category = Column(String(100))
    image_url = Column(Text)
    stock_count = Column(Integer, default=0)
    stock_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    type = Column(String(20), default="product")
    source = Column(String(20), default="web")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    from sqlalchemy.orm import validates

    @validates("stock_count")
    def sync_stock_count(self, key, value):
        if self.stock_quantity != value:
            self.stock_quantity = value
        return value

    @validates("stock_quantity")
    def sync_stock_quantity(self, key, value):
        if self.stock_count != value:
            self.stock_count = value
        return value
