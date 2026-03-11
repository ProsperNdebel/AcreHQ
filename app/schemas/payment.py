from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    ECOCASH = "ecocash"
    ONEMONEY = "onemoney"
    VISA = "visa"
    MASTERCARD = "mastercard"


# Schema for initiating payment
class PaymentInitiate(BaseModel):
    order_id: str


# Schema for payment response
class PaymentResponse(BaseModel):
    id: str
    order_id: str
    amount: float
    paynow_fee: float
    platform_fee: float
    total_amount: float
    paynow_reference: Optional[str]
    poll_url: Optional[str]
    redirect_url: Optional[str]
    payment_method: Optional[PaymentMethod]
    status: PaymentStatus
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Schema for payment status update (webhook)
class PaymentWebhook(BaseModel):
    reference: str
    paynowreference: str
    amount: str
    status: str
    pollurl: str
    hash: str