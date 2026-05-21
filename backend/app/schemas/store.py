from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StoreSetupRequest(BaseModel):
    business_description: str = Field(min_length=10, max_length=2000)


class StoreUpdateRequest(BaseModel):
    store_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
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


class StoreResponse(BaseModel):
    id: UUID
    store_name: str
    store_slug: str
    store_description: Optional[str] = None
    whatsapp_number: Optional[str] = None
    theme_config: dict = {}
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    is_active: bool = True
    is_published: bool = False
    products: list[ProductInStoreResponse] = []
    public_url: str = ""


class StoreDashboardStats(BaseModel):
    total_orders: int = 0
    pending_orders: int = 0
    today_revenue: float = 0.0
    total_revenue: float = 0.0
    product_count: int = 0


class StoreDashboardResponse(BaseModel):
    store: StoreResponse
    stats: StoreDashboardStats
