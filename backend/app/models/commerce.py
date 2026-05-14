import uuid

from sqlalchemy import JSON, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class Store(Base):
    __tablename__ = "stores"
    __table_args__ = (
        CheckConstraint("slug = lower(slug)", name="ck_stores_slug_lowercase"),
        #CheckConstraint("slug ~ '^[a-z0-9][a-z0-9-]*$'", name="ck_stores_slug_url_safe"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_name = Column(String(150), nullable=False)
    slug = Column(String(180), unique=True, nullable=False)
    store_slug = Column(String(180), unique=True)
    description = Column(Text)
    store_description = Column(Text)
    tagline = Column(String(255))
    theme_json = Column(JSON_TYPE, default=dict)
    theme = Column(String(50), default="default")
    contact_whatsapp = Column(String(20))
    whatsapp_number = Column(String(20))
    squad_virtual_account_id = Column(String(100))
    squad_virtual_account_number = Column(String(20))
    squad_customer_identifier = Column(String(120), unique=True)
    has_squad_account = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Product(Base):
    __tablename__ = "products"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    type = Column(String(20), default="product")
    price = Column(Numeric(12, 2), nullable=False)
    image_url = Column(Text)
    stock_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    source = Column(String(20), default="web")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Order(Base):
    __tablename__ = "orders"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    customer_name = Column(String(120))
    customer_phone = Column(String(20))
    customer_whatsapp = Column(String(20))
    total_amount = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(String(30), default="pending")
    order_status = Column(String(30), default="pending")
    status = Column(String(20), default="pending")
    squad_payment_reference = Column(String(120), unique=True)
    squad_transaction_ref = Column(String(100))
    payment_method = Column(String(20), default="transfer")
    notes = Column(Text)
    campaign_ref = Column(String(100))
    idempotency_key = Column(String(120), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True))


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(Uuid(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id"), nullable=False)
    movement_type = Column(String(30), nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(String(120))
    related_order_id = Column(Uuid(as_uuid=True), ForeignKey("orders.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
