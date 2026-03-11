from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.earning import FarmerEarning, EarningStatus
from app.api.deps import get_current_user

router = APIRouter()


# Simple admin check
def get_admin_user(current_user: User = Depends(get_current_user)):
    # TODO: Add proper admin role check
    return current_user


@router.get("/pending")
async def get_pending_payouts(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all farmers with pending payouts (admin only)
    """
    # Query pending earnings grouped by farmer
    pending = db.query(
        User.id,
        User.name,
        User.phone_number,
        func.sum(FarmerEarning.amount).label("total_amount"),
        func.count(FarmerEarning.id).label("transaction_count")
    ).join(
        FarmerEarning, FarmerEarning.farmer_id == User.id
    ).filter(
        FarmerEarning.status == EarningStatus.PENDING,
        User.user_type == "farmer"
    ).group_by(User.id, User.name, User.phone_number).all()
    
    # Format response
    farmers = []
    total = 0
    for farmer_id, name, phone, amount, count in pending:
        farmers.append({
            "farmer_id": farmer_id,
            "farmer_name": name,
            "phone_number": phone,
            "amount": float(amount),
            "transaction_count": count
        })
        total += float(amount)
    
    return {
        "farmers": farmers,
        "total_amount": total,
        "farmer_count": len(farmers)
    }


@router.post("/mark-paid")
async def mark_payouts_paid(
    farmer_ids: List[str],
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Mark pending payouts as paid for specified farmers (admin only)
    """
    # Update all pending earnings for these farmers
    updated_count = db.query(FarmerEarning).filter(
        FarmerEarning.farmer_id.in_(farmer_ids),
        FarmerEarning.status == EarningStatus.PENDING
    ).update({
        FarmerEarning.status: EarningStatus.PAID,
        FarmerEarning.paid_at: datetime.utcnow()
    }, synchronize_session=False)
    
    db.commit()
    
    return {
        "message": f"Marked {updated_count} transactions as paid",
        "farmers_updated": len(farmer_ids)
    }