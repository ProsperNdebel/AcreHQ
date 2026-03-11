from sqlalchemy import Column, String, Float, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.db.session import Base


class EarningStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"


class EarningType(str, enum.Enum):
    ORDER_COMMISSION = "order_commission"
    BONUS = "bonus"
    ADJUSTMENT = "adjustment"


class FarmerEarning(Base):
    __tablename__ = "farmer_earnings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farmer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=True)
    
    amount = Column(Float, nullable=False)
    type = Column(Enum(EarningType), default=EarningType.ORDER_COMMISSION, nullable=False)
    status = Column(Enum(EarningStatus), default=EarningStatus.PENDING, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Payout tracking
    payout_batch_id = Column(String(36), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    farmer = relationship("User", back_populates="earnings")
    order = relationship("Order", back_populates="earning")
    
    def __repr__(self):
        return f"<FarmerEarning {self.farmer_id} - ${self.amount} ({self.status})>"