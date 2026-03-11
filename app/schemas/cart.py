from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# Schema for adding item to cart
class CartItemCreate(BaseModel):
    listing_id: str
    quantity: float = Field(..., gt=0)


# Schema for updating cart item quantity
class CartItemUpdate(BaseModel):
    quantity: float = Field(..., gt=0)


# Schema for cart item response
class CartItemResponse(BaseModel):
    id: str
    user_id: str
    listing_id: str
    quantity: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Schema for cart item with listing details
class CartItemWithDetails(CartItemResponse):
    crop_name: str
    price_per_unit: float
    unit: str
    quantity_available: float
    images: list[str]
    farmer_id: str
    listing_status: str
    
    class Config:
        from_attributes = True