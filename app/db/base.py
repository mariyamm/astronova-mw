from app.db.database import Base


# Import all models here to make them available for Alembic
from models.user import User
from models.permission import Permission
from models.shopify_order import ShopifyOrder, Analysis, SolarReturnChart, SolarReturnReport, PdfJob

# This ensures all models are registered with SQLAlchemy
