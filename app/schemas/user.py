from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class UserType(str, Enum):
    FARMER = "farmer"
    CUSTOMER = "customer"


# Base schema
class UserBase(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    user_type: UserType


# Schema for user creation
class UserCreate(UserBase):
    pass


# Schema for user signup (phone only initially)
class UserSignup(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        # Remove spaces and special characters
        cleaned = ''.join(filter(str.isdigit, v))
        if not cleaned.startswith('263'):  # Zimbabwe country code
            if cleaned.startswith('0'):
                cleaned = '263' + cleaned[1:]
            else:
                cleaned = '263' + cleaned
        return cleaned


# Schema for OTP verification
class OTPVerify(BaseModel):
    phone_number: str
    otp_code: str = Field(..., min_length=6, max_length=6)


# Schema for completing profile after OTP
class UserProfileComplete(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    user_type: UserType
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_address: Optional[str] = None


# Schema for user update
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    profile_photo_url: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_address: Optional[str] = None
    payout_method: Optional[str] = None
    ecocash_number: Optional[str] = None
    onemoney_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None


# Schema for user response
class UserResponse(UserBase):
    id: str
    profile_photo_url: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_address: Optional[str] = None
    verified: bool
    active: bool
    created_at: datetime
    updated_at: datetime
    payout_method: Optional[str] = None
    ecocash_number: Optional[str] = None
    onemoney_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    
    class Config:
        from_attributes = True  # For Pydantic v2 (was orm_mode in v1)


# Schema for login response with token
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse