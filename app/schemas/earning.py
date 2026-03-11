from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class EarningStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"


class EarningType(str, Enum):
    ORDER_COMMISSION = "order_commission"
    BONUS = "bonus"
    ADJUSTMENT = "adjustment"


# Schema for earning response
class EarningResponse(BaseModel):
    id: str
    farmer_id: str
    order_id: Optional[str]
    amount: float
    type: EarningType
    status: EarningStatus
    description: Optional[str]
    payout_batch_id: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Schema for earnings summary
class EarningsSummary(BaseModel):
    balance: float  
    total_earnings: float  
    this_month: float  
    transactions: list[EarningResponse]


# Schema for transaction display (simplified)
class TransactionItem(BaseModel):
    id: str
    type: str  # "sale" or "withdrawal"
    amount: float
    description: str
    date: str
    status: str