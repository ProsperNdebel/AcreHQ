from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.db.session import get_db
from app.schemas.user import UserSignup, OTPVerify, UserProfileComplete, TokenResponse, UserResponse, UserUpdate
from app.schemas.notification import NotificationPreferences
from app.models.user import User
from app.core.security import create_access_token, generate_otp
from app.services.sms_service import sms_service
from app.api.deps import get_current_user

router = APIRouter()


# Temporary OTP storage (in production, use Redis or database)
otp_storage = {}

# Test accounts for Google Play review
TEST_ACCOUNTS = {
    "263771000001": "123456",  # test farmer
    "263771000002": "123456",  # test buyer
}


@router.post("/signup", status_code=status.HTTP_200_OK)
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone_number == user_data.phone_number).first()
    if existing_user and existing_user.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    otp_code = generate_otp()
    print(f'this is the phone numner: {user_data}')
    # Override OTP for test accounts
    if user_data.phone_number in TEST_ACCOUNTS:
        print('we are in here Prosper no need')
        otp_code = TEST_ACCOUNTS[user_data.phone_number]

    otp_storage[user_data.phone_number] = {
        "code": otp_code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    
    sms_sent = await sms_service.send_otp(user_data.phone_number, otp_code)
    
    if not sms_sent:
        print(f"OTP for {user_data.phone_number}: {otp_code}")
    
    return {
        "message": "OTP sent successfully",
        "phone_number": user_data.phone_number,
        **({"otp": otp_code} if not sms_sent else {})
    }


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(verify_data: OTPVerify, db: Session = Depends(get_db)):
    """
    Step 2: Verify OTP code
    """
    # Check if OTP exists
    if verify_data.phone_number not in otp_storage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    otp_data = otp_storage[verify_data.phone_number]
    
    # Check if OTP expired
    if datetime.utcnow() > otp_data["expires_at"]:
        del otp_storage[verify_data.phone_number]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired"
        )
    
    # Verify OTP code
    if otp_data["code"] != verify_data.otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
    
    # OTP verified, remove from storage
    del otp_storage[verify_data.phone_number]
    
    return {
        "message": "OTP verified successfully",
        "phone_number": verify_data.phone_number
    }


@router.post("/complete-profile", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def complete_profile(
    profile_data: UserProfileComplete,
    phone_number: str,
    db: Session = Depends(get_db)
):
    """
    Step 3: Complete user profile after OTP verification
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if existing_user:
        # Update existing user
        existing_user.name = profile_data.name
        existing_user.user_type = profile_data.user_type
        existing_user.location_lat = profile_data.location_lat
        existing_user.location_lng = profile_data.location_lng
        existing_user.location_address = profile_data.location_address
        existing_user.verified = True
        existing_user.active = True
        db.commit()
        db.refresh(existing_user)
        user = existing_user
    else:
        # Create new user
        new_user = User(
            phone_number=phone_number,
            name=profile_data.name,
            user_type=profile_data.user_type,
            location_lat=profile_data.location_lat,
            location_lng=profile_data.location_lng,
            location_address=profile_data.location_address,
            verified=True,
            active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    
    # Create access token
    access_token = create_access_token(subject=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user_data: UserSignup, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == user_data.phone_number).first()
    
    if not user or not user.verified:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sign up first."
        )
    
    otp_code = generate_otp()

    # Override OTP for test accounts
    if user_data.phone_number in TEST_ACCOUNTS:
        otp_code = TEST_ACCOUNTS[user_data.phone_number]

    otp_storage[user_data.phone_number] = {
        "code": otp_code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "user_id": str(user.id)
    }
    
    sms_sent = await sms_service.send_otp(user_data.phone_number, otp_code)
    
    if not sms_sent:
        print(f"Login OTP for {user_data.phone_number}: {otp_code}")
    
    return {
        "message": "OTP sent successfully",
        "phone_number": user_data.phone_number,
        **({"otp": otp_code} if not sms_sent else {})
    }


@router.post("/login-verify", response_model=TokenResponse)
async def login_verify(verify_data: OTPVerify, db: Session = Depends(get_db)):
    """
    Verify OTP and complete login
    """
    # Check if OTP exists
    if verify_data.phone_number not in otp_storage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    otp_data = otp_storage[verify_data.phone_number]
    
    # Check if OTP expired
    if datetime.utcnow() > otp_data["expires_at"]:
        del otp_storage[verify_data.phone_number]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired"
        )
    
    # Verify OTP code
    if otp_data["code"] != verify_data.otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
    
    # Get user
    user = db.query(User).filter(User.phone_number == verify_data.phone_number).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Clear OTP
    del otp_storage[verify_data.phone_number]
    
    # Create access token
    access_token = create_access_token(subject=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile
    """
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user



@router.get("/notification-preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's notification preferences
    """
    prefs = current_user.notification_preferences or {}
    return NotificationPreferences(**prefs)


@router.put("/notification-preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's notification preferences
    """
    current_user.notification_preferences = preferences.model_dump()
    db.commit()
    db.refresh(current_user)
    
    return NotificationPreferences(**current_user.notification_preferences)