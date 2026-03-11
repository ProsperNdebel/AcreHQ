from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, Enum, ForeignKey, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import func, Index
import uuid
import enum

from app.db.session import Base


class ListingType(str, enum.Enum):
    AVAILABLE_NOW = "available_now"
    PRE_ORDER = "pre_order"


class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    SOLD_OUT = "sold_out"
    EXPIRED = "expired"
    DELETED = "deleted"


class Listing(Base):
    __tablename__ = "listings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farmer_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    # Crop details
    crop_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Quantity and pricing
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # kg, bags, bundles, etc.
    price_per_unit = Column(Float, nullable=False)
    quantity_available = Column(Float, nullable=False)  # Tracks remaining quantity
    quantity_sold = Column(Float, default=0)
    
    # Listing type
    listing_type = Column(Enum(ListingType), nullable=False, index=True)
    harvest_date = Column(DateTime(timezone=True), nullable=True)  # For pre-orders
    
    # Status
    status = Column(Enum(ListingStatus), default=ListingStatus.ACTIVE, index=True)
    
    # Images (stored as JSON array of URLs)
    images = Column(Text, nullable=True)  # Comma-separated URLs for SQLite
    
    # Location (optional - can use farmer's location)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    
    # Metrics
    views = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Add to Listing model:
    orders = relationship("Order", back_populates="listing")

    cart_items = relationship("CartItem", back_populates="listing")

    # Add to Listing model:
    farmer = relationship("User", foreign_keys=[farmer_id], back_populates="listings")

    __table_args__ = (
        Index('idx_crop_name_lower', func.lower(crop_name)),
        Index('idx_status', status),                   
        Index('idx_listing_type', listing_type),        
        Index('idx_price_per_unit', price_per_unit), 
        Index('idx_farmer_id', farmer_id),      
        Index('idx_status_type', status, listing_type),
    )
    
    def __repr__(self):
        return f"<Listing {self.crop_name} - {self.quantity}{self.unit} @ ${self.price_per_unit}/{self.unit}>"