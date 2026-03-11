from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Schema for creating an order
class OrderCreate(BaseModel):
    listing_id: str
    quantity: float = Field(..., gt=0)


# Schema for updating order status
class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# Schema for order response
class OrderResponse(BaseModel):
    id: str
    listing_id: str
    customer_id: str
    farmer_id: str
    quantity: float
    unit: str
    price_per_unit: float
    total_price: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Schema for order with extra details
class OrderWithDetails(OrderResponse):
    crop_name: str
    customer_name: str
    customer_phone: str
    farmer_name: str
    farmer_phone: str
    
    class Config:
        from_attributes = True