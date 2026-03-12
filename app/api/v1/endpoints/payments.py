from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from paynow import Paynow
from datetime import datetime

from app.db.session import get_db
from app.schemas.payment import PaymentInitiate, PaymentResponse, PaymentWebhook
from app.models.payment import Payment, PaymentStatus
from app.models.order import Order
from app.models.user import User
from app.api.deps import get_current_customer
from app.core.config import settings

router = APIRouter()

# Mock mode detection
MOCK_MODE = settings.PAYNOW_INTEGRATION_ID == "12345"

# Initialize Paynow (only if not in mock mode)
# if not MOCK_MODE:
#     paynow = Paynow(
#         settings.PAYNOW_INTEGRATION_ID,
#         settings.PAYNOW_INTEGRATION_KEY,
#         settings.PAYNOW_RESULT_URL,
#         settings.PAYNOW_RETURN_URL
#     )

@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(
    payment_data: PaymentInitiate,
    current_customer: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Initiate a Paynow payment for an order
    """
    # Debug prints
    print(f"MOCK_MODE: {MOCK_MODE}")
    print(f"Integration ID: {settings.PAYNOW_INTEGRATION_ID}")
    print(f"Integration Key length: {len(settings.PAYNOW_INTEGRATION_KEY)}")
    print(f"Result URL: {settings.PAYNOW_RESULT_URL}")
    
    # Get the order
    order = db.query(Order).filter(Order.id == payment_data.order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if customer owns this order
    if order.customer_id != current_customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to pay for this order"
        )
    
    # Check if payment already exists
    existing_payment = db.query(Payment).filter(
        Payment.order_id == payment_data.order_id
    ).first()
    
    if existing_payment and existing_payment.status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already paid"
        )
    
    # Calculate fees
    order_amount = order.total_price
    paynow_fee = order_amount * 0.025  # 2.5% for mobile money
    platform_fee = order_amount * 0.05  # 5% platform commission
    total_amount = order_amount + paynow_fee + platform_fee
    
    # Create or update payment record
    if existing_payment:
        payment = existing_payment
        payment.status = PaymentStatus.PENDING
        payment.amount = order_amount
        payment.paynow_fee = paynow_fee
        payment.platform_fee = platform_fee
        payment.total_amount = total_amount
    else:
        payment = Payment(
            order_id=order.id,
            amount=order_amount,
            paynow_fee=paynow_fee,
            platform_fee=platform_fee,
            total_amount=total_amount,
            status=PaymentStatus.PENDING
        )
        db.add(payment)
    
    db.commit()
    db.refresh(payment)
    
    # Send payment to Paynow (or mock)
    try:
        if MOCK_MODE:
            # MOCK MODE - Simulate successful payment initiation
            payment.paynow_reference = f"MOCK-{payment.id[:8]}"
            payment.poll_url = f"http://mock.paynow.com/poll/{payment.id}"
            payment.redirect_url = f"myapp://payment-mock/{payment.id}"
            
            db.commit()
            db.refresh(payment)
            
            return payment
        else:
            # REAL PAYNOW MODE - Initialize Paynow object here
            paynow = Paynow(
                settings.PAYNOW_INTEGRATION_ID,
                settings.PAYNOW_INTEGRATION_KEY,
                settings.PAYNOW_RETURN_URL,
                settings.PAYNOW_RESULT_URL,
            )
            
            print(f"Paynow initialized with Result URL: {settings.PAYNOW_RESULT_URL}")
            
            print("Creating Paynow payment object...")
            paynow_payment = paynow.create_payment(
                reference=payment.id,
                auth_email=current_customer.phone_number
            )
            
            print(f"Adding item: Order {order.id[:8]} - {order.listing.crop_name}")
            # Add item
            paynow_payment.add(
                f"Order {order.id[:8]} - {order.listing.crop_name}",
                total_amount
            )
            
            print("Sending to Paynow...")
            print(f"Paynow result_url: {paynow.result_url}")
            print(f"Paynow return_url: {paynow.return_url}")
            response = paynow.send(paynow_payment)
            
            print(f"Paynow response success: {response.success}")
            if hasattr(response, 'errors'):
                print(f"Paynow errors: {response.error}")
            if hasattr(response, 'data'):
                print(f"Paynow data: {response.data}")
            
            if response.success:
                payment.paynow_reference = response.data.get('paynowreference')
                payment.poll_url = response.data.get('pollurl')
                payment.redirect_url = response.redirect_url
                
                db.commit()
                db.refresh(payment)
                
                return payment
            else:
                payment.status = PaymentStatus.FAILED
                db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Payment initiation failed: {response.error}"
                )
    except HTTPException:
        raise
    except Exception as e:
        print(f"FULL ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        payment.status = PaymentStatus.FAILED
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment error: {str(e)}"
        )


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Paynow webhook for payment status updates
    """
    # Get form data from webhook
    form_data = await request.form()
    webhook_data = dict(form_data)
    
    # Extract payment reference (our payment ID)
    reference = webhook_data.get('reference')
    paynow_reference = webhook_data.get('paynowreference')
    status_str = webhook_data.get('status')
    
    if not reference:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing reference"
        )
    
    # Get payment
    payment = db.query(Payment).filter(Payment.id == reference).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Update payment status based on Paynow response
    if status_str.lower() == "paid":
        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.utcnow()
        
        # Update order status to ACCEPTED (farmer can now prepare)
        order = payment.order
        if order:
            order.status = "accepted"
    elif status_str.lower() in ["cancelled", "failed"]:
        payment.status = PaymentStatus.FAILED
    
    db.commit()
    
    return {"message": "Webhook processed"}


@router.post("/mock-confirm/{payment_id}")
async def mock_confirm_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """
    MOCK ONLY - Simulate successful payment (for testing)
    """
    if not MOCK_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock endpoints only available in mock mode"
        )
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Simulate successful payment
    payment.status = PaymentStatus.PAID
    payment.paid_at = datetime.utcnow()
    
    # Update order status
    order = payment.order
    if order:
        order.status = "accepted"
    
    db.commit()
    db.refresh(payment)
    
    return {
        "message": "Mock payment confirmed",
        "payment_id": payment.id,
        "status": payment.status,
        "order_status": order.status if order else None
    }


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_customer: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Get payment details
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check if customer owns this payment
    if payment.order.customer_id != current_customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment"
        )
    
    return payment


@router.get("/order/{order_id}", response_model=PaymentResponse)
async def get_payment_by_order(
    order_id: str,
    current_customer: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Get payment details by order ID
    """
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found for this order"
        )
    
    # Check if customer owns this payment
    if payment.order.customer_id != current_customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment"
        )
    
    return payment

@router.get("/payment-return")
async def payment_return(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="acrehq://payment-return")