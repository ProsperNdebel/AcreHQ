from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.api.deps import get_current_user
import json

from app.db.session import get_db
from app.schemas.listing import ListingCreate, ListingUpdate, ListingResponse, ListingListItem
from app.models.listing import Listing, ListingType, ListingStatus
from app.models.user import User
from app.api.deps import get_current_user, get_current_farmer

router = APIRouter()


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    listing_data: ListingCreate,
    current_farmer: User = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """
    Create a new listing (farmers only)
    """
    # Create new listing
    new_listing = Listing(
        farmer_id=current_farmer.id,
        crop_name=listing_data.crop_name,
        description=listing_data.description,
        quantity=listing_data.quantity,
        unit=listing_data.unit,
        price_per_unit=listing_data.price_per_unit,
        quantity_available=listing_data.quantity,  # Initially all quantity is available
        listing_type=listing_data.listing_type,
        harvest_date=listing_data.harvest_date,
        images=json.dumps(listing_data.images) if listing_data.images else None,
        location_lat=listing_data.location_lat or current_farmer.location_lat,
        location_lng=listing_data.location_lng or current_farmer.location_lng,
        status=ListingStatus.ACTIVE
    )
    
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    
    # Parse images back to list for response
    listing_dict = {
        **new_listing.__dict__,
        'images': json.loads(new_listing.images) if new_listing.images else []
    }
    response = ListingResponse.model_validate(listing_dict)
    
    return response

@router.get("/", response_model=List[ListingResponse])
async def get_listings(
    listing_type: Optional[ListingType] = None,
    status: Optional[ListingStatus] = Query(default=ListingStatus.ACTIVE),
    crop_name: Optional[str] = None,
    categories: Optional[str] = Query(None),  # Comma-separated: "vegetables,fruits"
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all listings with filters - includes farmer location
    Supports: search, categories, price range, pagination
    """
    # Join with User table to get farmer location
    query = db.query(
        Listing,
        User.location_lat,
        User.location_lng,
        User.location_address,
        User.name,                    
        User.phone_number,            
        User.profile_photo_url
    ).join(User, Listing.farmer_id == User.id)
    
    # Filter by status
    if status:
        query = query.filter(Listing.status == status)
    
    # Filter by listing type
    if listing_type:
        query = query.filter(Listing.listing_type == listing_type)
    
    # Search in crop name AND description
    if crop_name:
        search_term = f"%{crop_name}%"
        query = query.filter(
            or_(
                Listing.crop_name.ilike(search_term),
                Listing.description.ilike(search_term)
            )
        )
    
    # Filter by categories
    if categories:
        category_list = [cat.strip() for cat in categories.split(',')]
        category_patterns = []
        
        for category in category_list:
            if category == "vegetables":
                patterns = ["tomato", "cabbage", "lettuce", "carrot", "spinach", "kale", 
                           "broccoli", "cauliflower", "pepper", "onion", "potato"]
            elif category == "fruits":
                patterns = ["apple", "banana", "orange", "mango", "grape", "strawberry",
                           "watermelon", "pineapple", "papaya", "avocado"]
            elif category == "grains":
                patterns = ["wheat", "rice", "corn", "maize", "barley", "oats", "sorghum", "millet"]
            elif category == "herbs":
                patterns = ["basil", "mint", "parsley", "cilantro", "thyme", "rosemary",
                           "sage", "oregano", "dill"]
            else:
                continue
            
            # Add all patterns for this category
            for pattern in patterns:
                category_patterns.append(Listing.crop_name.ilike(f"%{pattern}%"))
        
        if category_patterns:
            query = query.filter(or_(*category_patterns))
    
    # Filter by price range
    if min_price is not None:
        query = query.filter(Listing.price_per_unit >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price_per_unit <= max_price)
    
    # Pagination
    results = query.offset(skip).limit(limit).all()
    
    # Build response with farmer location
    response_list = []
    for listing, farmer_lat, farmer_lng, farmer_address, farmer_name, farmer_phone, farmer_photo in results:
        listing_dict = {
            **listing.__dict__,
            'images': json.loads(listing.images) if listing.images else [],
            'farmer_location_lat': farmer_lat,
            'farmer_location_lng': farmer_lng,
            'farmer_location_address': farmer_address,
            'farmer_name': farmer_name,
            'farmer_phone': farmer_phone,
            'farmer_photo_url': farmer_photo,
        }
        response_list.append(ListingResponse.model_validate(listing_dict))
    
    return response_list

@router.get("/my-listings", response_model=List[ListingListItem])
async def get_my_listings(
    current_farmer: User = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """
    Get all listings for the current farmer
    """
    listings = db.query(Listing).filter(
        Listing.farmer_id == current_farmer.id
    ).order_by(Listing.created_at.desc()).all()
    
    # Parse images for each listing
    result = []
    for listing in listings:
        listing_dict = {
            **listing.__dict__,
            'images': json.loads(listing.images) if listing.images else []
        }
        item = ListingListItem.model_validate(listing_dict)
        result.append(item)
    
    return result


@router.put("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: str,
    listing_data: ListingUpdate,
    current_farmer: User = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """
    Update a listing (owner only)
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    if listing.farmer_id != current_farmer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own listings"
        )
    
    # Update fields
    update_data = listing_data.model_dump(exclude_unset=True)
    
    # Handle images separately
    if 'images' in update_data:
        update_data['images'] = json.dumps(update_data['images'])
    
    for field, value in update_data.items():
        setattr(listing, field, value)
    
    db.commit()
    db.refresh(listing)
    
    # Parse images
    listing_dict = {
        **listing.__dict__,
        'images': json.loads(listing.images) if listing.images else []
    }
    response = ListingResponse.model_validate(listing_dict)
    
    return response

@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: str,
    current_farmer: User = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """
    Delete a listing (owner only) - soft delete by marking as deleted
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    if listing.farmer_id != current_farmer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own listings"
        )
    
    # NEW: Check for active orders
    from app.models.order import Order
    
    active_orders = db.query(Order).filter(
        Order.listing_id == listing_id,
        Order.status.in_(['pending', 'accepted', 'ready'])
    ).count()
    
    if active_orders > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete listing with {active_orders} active order(s). Please complete or cancel them first."
        )
    
    # Soft delete
    listing.status = ListingStatus.DELETED
    db.commit()
    
    return None

@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get a specific listing by ID - includes farmer info
    """
    # Join with User table to get farmer info
    result = db.query(
        Listing,
        User.location_lat,
        User.location_lng,
        User.location_address,
        User.name,
        User.phone_number,
        User.profile_photo_url
    ).join(User, Listing.farmer_id == User.id).filter(
        Listing.id == listing_id
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    listing, farmer_lat, farmer_lng, farmer_address, farmer_name, farmer_phone, farmer_photo = result
    
    # Increment view count only if not the owner
    if not current_user or current_user.id != listing.farmer_id:
        listing.views += 1
        db.commit()
        db.refresh(listing)
    
    # Parse images and add farmer info
    listing_dict = {
        **listing.__dict__,
        'images': json.loads(listing.images) if listing.images else [],
        'farmer_location_lat': farmer_lat,
        'farmer_location_lng': farmer_lng,
        'farmer_location_address': farmer_address,
        'farmer_name': farmer_name,
        'farmer_phone': farmer_phone,
        'farmer_photo_url': farmer_photo,
    }
    response = ListingResponse.model_validate(listing_dict)
    
    return response