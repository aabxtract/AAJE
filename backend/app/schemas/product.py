from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: float = Field(gt=0)
    category: Optional[str] = Field(default=None, max_length=100)
    stock_count: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=2000)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = Field(default=None, max_length=100)
    stock_count: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=2000)
    is_available: Optional[bool] = None


class ProductResponse(BaseModel):
    id: UUID
    store_id: UUID
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    image_url: Optional[str] = None
    stock_count: Optional[int] = None
    is_available: bool
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
