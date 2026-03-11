from sqlalchemy import Column, String, Boolean, DateTime, Float, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.db.session import Base


class UserType(str, enum.Enum):
    FARMER = "farmer"
    CUSTOMER = "customer"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    user_type = Column(Enum(UserType), nullable=False, index=True)
    profile_photo_url = Column(String, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    location_address = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # Add to User model:
    customer_orders = relationship("Order", foreign_keys="Order.customer_id", back_populates="customer")
    farmer_orders = relationship("Order", foreign_keys="Order.farmer_id", back_populates="farmer")
    cart_items = relationship("CartItem", back_populates="user")
    # Add to User model:
    listings = relationship("Listing", foreign_keys="Listing.farmer_id", back_populates="farmer")
    earnings = relationship("FarmerEarning", back_populates="farmer")

    notification_preferences = Column(JSON, default={
    "order_updates": True,
    "new_orders": True,
    "payment_notifications": True,
    "new_listings": True,
    "messages": True,
    "promotional": False,
    "listing_performance": True,
})
    payout_method = Column(String(20), nullable=True)  # 'ecocash', 'onemoney', 'bank'
    ecocash_number = Column(String(20), nullable=True)
    onemoney_number = Column(String(20), nullable=True)
    bank_name = Column(String(100), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    bank_account_name = Column(String(100), nullable=True)
    def __repr__(self):
        return f"<User {self.name} ({self.phone_number})>"