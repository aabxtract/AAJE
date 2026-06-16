import uuid

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, Uuid

from app.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(Uuid(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id"))
    product_name = Column(String(200), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=True)

    from sqlalchemy.orm import validates

    @validates("total_price", "subtotal")
    def sync_prices(self, key, value):
        if getattr(self, "_syncing_price", False):
            return value
        self._syncing_price = True
        try:
            if key == "total_price":
                self.subtotal = value
            elif key == "subtotal":
                self.total_price = value
        finally:
            self._syncing_price = False
        return value
