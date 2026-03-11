from app.db.session import engine, Base
from app.models.user import User
from app.models.listing import Listing
from app.models.order import Order
from app.models.cart import CartItem
from app.models.earning import FarmerEarning
from app.models.payment import Payment

# Import all models here so SQLAlchemy knows about them
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully!")