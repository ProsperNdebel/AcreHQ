from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class ListingType(str, Enum):
    AVAILABLE_NOW = "available_now"
    PRE_ORDER = "pre_order"


class ListingStatus(str, Enum):
    ACTIVE = "active"
    SOLD_OUT = "sold_out"
    EXPIRED = "expired"
    DELETED = "deleted"


# Base schema
class ListingBase(BaseModel):
    crop_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)
    price_per_unit: float = Field(..., gt=0)
    listing_type: ListingType
    harvest_date: Optional[datetime] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


# Schema for creating a listing
class ListingCreate(ListingBase):
    images: Optional[List[str]] = []  # List of image URLs
    
    @field_validator('harvest_date')
    @classmethod
    def validate_harvest_date(cls, v, info):
        if info.data.get('listing_type') == ListingType.PRE_ORDER and not v:
            raise ValueError('harvest_date is required for pre-order listings')
        if info.data.get('listing_type') == ListingType.AVAILABLE_NOW and v:
            raise ValueError('harvest_date should not be set for available_now listings')
        return v


# Schema for updating a listing
class ListingUpdate(BaseModel):
    crop_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    price_per_unit: Optional[float] = Field(None, gt=0)
    listing_type: Optional[ListingType] = None
    harvest_date: Optional[datetime] = None
    status: Optional[ListingStatus] = None
    images: Optional[List[str]] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


# Schema for listing response
class ListingResponse(ListingBase):
    id: str
    farmer_id: str
    quantity_available: float
    quantity_sold: float
    status: ListingStatus
    images: List[str] = []
    views: int
    created_at: datetime
    updated_at: datetime
    farmer_location_lat: Optional[float] = None
    farmer_location_lng: Optional[float] = None
    farmer_location_address: Optional[str] = None
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    farmer_photo_url: Optional[str] = None
    
    class Config:
        from_attributes = True


# Schema for listing list (simplified)
class ListingListItem(BaseModel):
    id: str
    farmer_id: str
    crop_name: str
    quantity: float
    unit: str
    price_per_unit: float
    listing_type: ListingType
    harvest_date: Optional[datetime]
    status: ListingStatus
    images: List[str] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


# Schema for listing with farmer info
class ListingWithFarmer(ListingResponse):
    farmer_name: str
    farmer_photo: Optional[str]
    farmer_location: Optional[str]