import uuid

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, Uuid

from app.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(Uuid(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id"))
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
