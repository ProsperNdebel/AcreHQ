from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.order import OrderCreate, OrderStatusUpdate, OrderResponse, OrderWithDetails
from app.models.order import Order, OrderStatus
from app.models.listing import Listing
from app.models.user import User
from app.api.deps import get_current_user, get_current_customer, get_current_farmer
from app.services.sms_service import sms_service

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_customer: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Create a new order (customers only)
    """
    # Get listing
    listing = db.query(Listing).filter(Listing.id == order_data.listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    # Check if listing is active
    if listing.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing is not available"
        )
    
    # Check quantity available
    if order_data.quantity > listing.quantity_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {listing.quantity_available}{listing.unit} available"
        )
    
    # Calculate total price
    total_price = order_data.quantity * listing.price_per_unit
    
    # Create order
    new_order = Order(
        listing_id=listing.id,
        customer_id=current_customer.id,
        farmer_id=listing.farmer_id,
        quantity=order_data.quantity,
        unit=listing.unit,
        price_per_unit=listing.price_per_unit,
        total_price=total_price,
        status=OrderStatus.PENDING
    )
    
    # Update listing quantities
    listing.quantity_available -= order_data.quantity
    listing.quantity_sold += order_data.quantity
    
    # Check if sold out
    if listing.quantity_available <= 0:
        listing.status = "sold_out"
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    await sms_service.notify_order_placed(
    farmer_phone=listing.farmer.phone_number,
    crop_name=listing.crop_name,
    quantity=new_order.quantity,
    unit=new_order.unit
)
    return new_order


@router.get("/my-orders", response_model=List[OrderWithDetails])
async def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all orders for current user (farmer sees received orders, customer sees placed orders)
    """
    if current_user.user_type == "farmer":
        orders = db.query(Order).filter(
            Order.farmer_id == current_user.id
        ).order_by(Order.created_at.desc()).all()
    else:
        orders = db.query(Order).filter(
            Order.customer_id == current_user.id
        ).order_by(Order.created_at.desc()).all()
    
    # Build response with details
    result = []
    for order in orders:
        order_dict = {
            **order.__dict__,
            'crop_name': order.listing.crop_name,
            'customer_name': order.customer.name,
            'customer_phone': order.customer.phone_number,
            'farmer_name': order.farmer.name,
            'farmer_phone': order.farmer.phone_number,
        }
        result.append(OrderWithDetails(**order_dict))
    
    return result


@router.get("/{order_id}", response_model=OrderWithDetails)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific order by ID
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if user is authorized (either customer or farmer of this order)
    if order.customer_id != current_user.id and order.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    # Build response with details
    order_dict = {
        **order.__dict__,
        'crop_name': order.listing.crop_name,
        'customer_name': order.customer.name,
        'customer_phone': order.customer.phone_number,
        'farmer_name': order.farmer.name,
        'farmer_phone': order.farmer.phone_number,
    }
    
    return OrderWithDetails(**order_dict)


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    current_farmer: User = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """
    Update order status (farmers only)
    """
    from app.models.earning import FarmerEarning, EarningType, EarningStatus
    
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if farmer owns this order
    if order.farmer_id != current_farmer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own orders"
        )
    
    # Update status
    order.status = status_update.status
    
    # NEW: Create earnings when order is completed
    if status_update.status == OrderStatus.COMPLETED:
        # Calculate platform commission (5%)
        platform_commission = order.total_price * 0.05
        farmer_earnings = order.total_price - platform_commission
        
        earning = FarmerEarning(
            farmer_id=order.farmer_id,
            order_id=order.id,
            amount=farmer_earnings,
            type=EarningType.ORDER_COMMISSION,
            status=EarningStatus.PENDING,
            description=f"Order #{order.id[:8]} - {order.listing.crop_name}"
        )
        db.add(earning)
    
    db.commit()
    db.refresh(order)
    
    # Send notifications
    if order.status == OrderStatus.ACCEPTED:
        await sms_service.notify_order_accepted(
            customer_phone=order.customer.phone_number,
            crop_name=order.listing.crop_name
        )
    elif order.status == OrderStatus.READY:
        await sms_service.notify_order_ready(
            customer_phone=order.customer.phone_number,
            crop_name=order.listing.crop_name
        )
    elif order.status == OrderStatus.COMPLETED:
        await sms_service.notify_order_completed(
            farmer_phone=order.farmer.phone_number,
            customer_phone=order.customer.phone_number,
            crop_name=order.listing.crop_name
        )

    return order