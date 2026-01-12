"""
Restaurant Reservation System Backend API

A comprehensive reservation management system built with FastAPI and SQLite.
Provides full CRUD operations for restaurants, tables, customers, and bookings
with intelligent availability checking and automatic table assignment.
"""

__version__ = "1.0.0"
__author__ = "Restaurant Reservation System"
__description__ = "Backend API for managing restaurant reservations"

# Package-level imports for easier access
from .database import engine, SessionLocal, Base
from .models import Restaurant, Table, Customer, Booking
from .schemas import (
    RestaurantCreate,
    RestaurantUpdate,
    Restaurant as RestaurantResponse,
    TableCreate,
    TableUpdate,
    Table as TableResponse,
    CustomerCreate,
    CustomerUpdate,
    Customer as CustomerResponse,
    BookingCreate,
    BookingUpdate,
    Booking as BookingResponse,
    AvailabilityQuery,
    AvailabilityResponse
)
# Services are imported directly in route handlers where needed
# from .services import (
#     RestaurantService,
#     TableService,
#     CustomerService,
#     BookingService,
#     AvailabilityService
# )

# Export main components
__all__ = [
    # Database
    "engine",
    "SessionLocal",
    "Base",
    
    # Models
    "Restaurant",
    "Table",
    "Customer",
    "Booking",
    
    # Schemas
    "RestaurantCreate",
    "RestaurantUpdate",
    "RestaurantResponse",
    "TableCreate",
    "TableUpdate",
    "TableResponse",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "BookingCreate",
    "BookingUpdate",
    "BookingResponse",
    "AvailabilityQuery",
    "AvailabilityResponse",
]

# Initialize database tables on import
def init_db():
    """Initialize database tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

# Run initialization
init_db()