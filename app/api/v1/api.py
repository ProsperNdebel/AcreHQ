from fastapi import APIRouter
from app.api.v1.endpoints import listings
from app.api.v1.endpoints import auth 
from app.api.v1.endpoints import auth, listings, orders, upload, cart, earning, payouts, payments

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
# Include listings routes
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(earning.router, prefix="/earnings", tags=["earnings"])
api_router.include_router(payouts.router, prefix="/payouts", tags=["payouts"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
# More routers will be added as we build them
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
# api_router.include_router(orders.router, prefix="/orders", tags=["orders"])