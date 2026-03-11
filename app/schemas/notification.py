from pydantic import BaseModel
from typing import Optional


class NotificationPreferences(BaseModel):
    order_updates: Optional[bool] = True
    new_orders: Optional[bool] = True
    payment_notifications: Optional[bool] = True
    new_listings: Optional[bool] = True
    messages: Optional[bool] = True
    promotional: Optional[bool] = False
    listing_performance: Optional[bool] = True