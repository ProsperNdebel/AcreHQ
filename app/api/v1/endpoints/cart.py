from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from app.db.session import get_db
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartItemWithDetails
from app.models.cart import CartItem
from app.models.listing import Listing
from app.models.user import User
from app.api.deps import get_current_user, get_current_customer

router = APIRouter()


@router.get("/", response_model=List[CartItemWithDetails])
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's cart items with listing details
    """
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()
    
    # Build response with listing details
    result = []
    for item in cart_items:
        listing = item.listing
        
        # Skip if listing no longer exists or is inactive
        if not listing or listing.status != "active":
            continue
            
        item_dict = {
            **item.__dict__,
            'crop_name': listing.crop_name,
            'price_per_unit': listing.price_per_unit,
            'unit': listing.unit,
            'quantity_available': listing.quantity_available,
            'images': json.loads(listing.images) if listing.images else [],
            'farmer_id': listing.farmer_id,
            'listing_status': listing.status,
        }
        result.append(CartItemWithDetails(**item_dict))
    
    return result


@router.post("/", response_model=CartItemWithDetails)
async def add_to_cart(
    item_data: CartItemCreate,
    current_customer: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Add item to cart (customers only)
    """
    # Get listing
    listing = db.query(Listing).filter(Listing.id == item_data.listing_id).first()
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
    if item_data.quantity > listing.quantity_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {listing.quantity_available}{listing.unit} available"
        )
    
    # Check if item already in cart
    existing_item = db.query(CartItem).filter(
        CartItem.user_id == current_customer.id,
        CartItem.listing_id == item_data.listing_id
    ).first()
    
    if existing_item:
        # Update quantity
        new_quantity = existing_item.quantity + item_data.quantity
        
        if new_quantity > listing.quantity_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {listing.quantity_available}{listing.unit} available"
            )
        
        existing_item.quantity = new_quantity
        db.commit()
        db.refresh(existing_item)
        cart_item = existing_item
    else:
        # Create new cart item
        cart_item = CartItem(
            user_id=current_customer.id,
            listing_id=listing.id,
            quantity=item_data.quantity
        )
        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)
    
    # Build response with details
    item_dict = {
        **cart_item.__dict__,
        'crop_name': listing.crop_name,
        'price_per_unit': listing.price_per_unit,
        'unit': listing.unit,
        'quantity_available': listing.quantity_available,
        'images': json.loads(listing.images) if listing.images else [],
        'farmer_id': listing.farmer_id,
        'listing_status': listing.status,
    }
    
    return CartItemWithDetails(**item_dict)


@router.put("/{item_id}", response_model=CartItemWithDetails)
async def update_cart_item(
    item_id: str,
    update_data: CartItemUpdate,
    current_customer: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Update cart item quantity
    """
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_customer.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    listing = cart_item.listing
    
    # Check quantity available
    if update_data.quantity > listing.quantity_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {listing.quantity_available}{listing.unit} available"
        )
    
    cart_item.quantity = update_data.quantity
    db.commit()
    db.refresh(cart_item)
    
    # Build response with details
    item_dict = {
        **cart_item.__dict__,
        'crop_name': listing.crop_name,
        'price_per_unit': listing.price_per_unit,
        'unit': listing.unit,
        'quantity_available': listing.quantity_available,
        'images': json.loads(listing.images) if listing.images else [],
        'farmer_id': listing.farmer_id,
        'listing_status': listing.status,
    }
    
    return CartItemWithDetails(**item_dict)


@router.delete("/{item_id}")
async def remove_from_cart(
    item_id: str,
    current_customer: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Remove item from cart
    """
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_customer.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    db.delete(cart_item)
    db.commit()
    
    return {"message": "Item removed from cart"}


@router.delete("/")
async def clear_cart(
    current_customer: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Clear all items from cart
    """
    db.query(CartItem).filter(CartItem.user_id == current_customer.id).delete()
    db.commit()
    
    return {"message": "Cart cleared"}