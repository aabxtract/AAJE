from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class StoreSetupRequest(BaseModel):
    business_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    business_type: str = Field(default="physical_products", max_length=40)
    business_description: str = Field(min_length=10, max_length=2000)
    instagram_handle: Optional[str] = Field(default=None, max_length=120)
    whatsapp_number: Optional[str] = Field(default=None, max_length=20)


class StoreUpdateRequest(BaseModel):
    store_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    business_type: Optional[str] = Field(default=None, max_length=40)
    instagram_handle: Optional[str] = Field(default=None, max_length=120)
    store_description: Optional[str] = Field(default=None, max_length=2000)
    whatsapp_number: Optional[str] = Field(default=None, max_length=20)
    theme_config: Optional[dict] = None


class ProductInStoreResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    image_url: Optional[str] = None
    stock_count: Optional[int] = None
    is_available: bool

    model_config = {"from_attributes": True}

    @field_validator("is_available", mode="before")
    @classmethod
    def _coerce_none_available(cls, v):
        return True if v is None else v


class PaymentAccount(BaseModel):
    """Public bank-transfer destination shown on the storefront checkout."""

    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    ready: bool = False


class StoreResponse(BaseModel):
    id: UUID
    store_name: str
    store_slug: str
    business_type: str = "physical_products"
    instagram_handle: Optional[str] = None
    store_description: Optional[str] = None
    whatsapp_number: Optional[str] = None
    theme_config: dict = {}
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    is_active: bool = True
    is_published: bool = False
    products: list[ProductInStoreResponse] = []
    public_url: str = ""
    payment_account: PaymentAccount = PaymentAccount()

    # Legacy rows may have NULL for these columns — Pydantic v2 won't fall
    # back to the field default when the value is present-but-None. Coerce
    # at the schema layer so /store/me/dashboard doesn't 500 for old stores.
    @field_validator("is_active", mode="before")
    @classmethod
    def _coerce_none_active(cls, v):
        return True if v is None else v

    @field_validator("is_published", mode="before")
    @classmethod
    def _coerce_none_published(cls, v):
        return False if v is None else v

    @field_validator("theme_config", mode="before")
    @classmethod
    def _coerce_none_theme(cls, v):
        return {} if v is None else v


class StoreDashboardStats(BaseModel):
    total_orders: int = 0
    orders_today: int = 0
    pending_orders: int = 0
    today_revenue: float = 0.0
    total_revenue: float = 0.0
    product_count: int = 0
    low_stock_products: int = 0


class StoreDashboardResponse(BaseModel):
    store: StoreResponse
    stats: StoreDashboardStats
