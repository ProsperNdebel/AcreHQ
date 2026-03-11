from sqlalchemy import Column, String, Float, Enum, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.db.session import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    ECOCASH = "ecocash"
    ONEMONEY = "onemoney"
    VISA = "visa"
    MASTERCARD = "mastercard"


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, unique=True)
    
    # Payment details
    amount = Column(Float, nullable=False)
    paynow_fee = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Paynow tracking
    paynow_reference = Column(String(100), nullable=True)  # Paynow's reference
    poll_url = Column(Text, nullable=True)  # URL to check payment status
    redirect_url = Column(Text, nullable=True)  # URL to redirect user for payment
    
    # Payment method & status
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Timestamps
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    order = relationship("Order", back_populates="payment")
    
    def __repr__(self):
        return f"<Payment {self.id} - Order {self.order_id} - ${self.total_amount} ({self.status})>"