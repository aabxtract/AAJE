from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class OrderItemRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(ge=1, le=1000)


class OrderCreateRequest(BaseModel):
    store_slug: str = Field(min_length=1, max_length=100)
    customer_name: str = Field(min_length=1, max_length=100)
    customer_whatsapp: Optional[str] = Field(default=None, min_length=10, max_length=20)
    customer_email: Optional[EmailStr] = None
    items: list[OrderItemRequest] = Field(min_length=1, max_length=50)
    delivery_address: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("customer_whatsapp")
    @classmethod
    def normalize_whatsapp(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 10:
            raise ValueError("WhatsApp number must contain at least 10 digits")
        return digits


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: Optional[UUID] = None
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: UUID
    order_ref: str
    store_id: UUID
    customer_name: Optional[str] = None
    customer_whatsapp: Optional[str] = None
    customer_email: Optional[str] = None
    total_amount: float
    status: str
    payment_status: str
    payment_link: Optional[str] = None
    notes: Optional[str] = None
    delivery_address: Optional[str] = None
    items: list[OrderItemResponse] = []
    created_at: datetime


class OrderStatusUpdate(BaseModel):
    status: Literal["pending", "paid", "delivered", "cancelled"]


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int
    limit: int
    offset: int
