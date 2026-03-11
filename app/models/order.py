from sqlalchemy import Column, String, Float, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.db.session import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id = Column(String(36), ForeignKey("listings.id"), nullable=False)
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    farmer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    listing = relationship("Listing", back_populates="orders")
    customer = relationship("User", foreign_keys=[customer_id], back_populates="customer_orders")
    farmer = relationship("User", foreign_keys=[farmer_id], back_populates="farmer_orders")

    earning = relationship("FarmerEarning", back_populates="order", uselist=False)
    payment = relationship("Payment", back_populates="order", uselist=False)