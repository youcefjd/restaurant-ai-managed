"""
Restaurant Reservation System Backend API

A comprehensive reservation management system built with FastAPI and Supabase.
Provides full CRUD operations for restaurants, tables, customers, and bookings
with intelligent availability checking and automatic table assignment.
"""

__version__ = "1.0.0"
__author__ = "Restaurant Reservation System"
__description__ = "Backend API for managing restaurant reservations"

# Package-level imports for easier access
from .database import SupabaseDB, init_db, check_connection
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

# Export main components
__all__ = [
    # Database
    "SupabaseDB",
    "init_db",
    "check_connection",

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
