import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.sql import func

from app.database import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    movement_type = Column(String(30), nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(Text)
    related_order_id = Column(Uuid(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
