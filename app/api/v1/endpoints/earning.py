from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.earning import FarmerEarning, EarningStatus
from app.schemas.earning import EarningsSummary, EarningResponse, TransactionItem
from app.api.deps import get_current_farmer

router = APIRouter()


@router.get("/me", response_model=EarningsSummary)
async def get_my_earnings(
    current_farmer: User = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """
    Get current farmer's earnings summary and transaction history
    """
    # Get all earnings for this farmer
    earnings = db.query(FarmerEarning).filter(
        FarmerEarning.farmer_id == current_farmer.id
    ).order_by(FarmerEarning.created_at.desc()).all()
    
    # Calculate pending balance (unpaid earnings)
    pending_earnings = db.query(func.sum(FarmerEarning.amount)).filter(
        FarmerEarning.farmer_id == current_farmer.id,
        FarmerEarning.status == EarningStatus.PENDING
    ).scalar() or 0
    
    # Calculate total earnings (all time)
    total_earnings = db.query(func.sum(FarmerEarning.amount)).filter(
        FarmerEarning.farmer_id == current_farmer.id
    ).scalar() or 0
    
    # Calculate this month's earnings
    this_month_earnings = db.query(func.sum(FarmerEarning.amount)).filter(
        FarmerEarning.farmer_id == current_farmer.id,
        func.extract('month', FarmerEarning.created_at) == datetime.now().month,
        func.extract('year', FarmerEarning.created_at) == datetime.now().year
    ).scalar() or 0
    
    # Format transactions for mobile app
    transactions = [EarningResponse.model_validate(earning) for earning in earnings]
    
    return EarningsSummary(
        balance=float(pending_earnings),
        total_earnings=float(total_earnings),
        this_month=float(this_month_earnings),
        transactions=transactions
    )