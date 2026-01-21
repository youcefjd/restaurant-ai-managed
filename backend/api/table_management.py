"""
Table Management API
Allows restaurants to manually control table availability, block time slots, etc.
"""

from typing import List
from datetime import datetime, time as dt_time
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.database import get_db, SupabaseDB
from backend.services.table_availability import table_availability_service

router = APIRouter()


class TableCreate(BaseModel):
    """Schema for creating a new table"""
    restaurant_id: int
    table_number: str
    capacity: int
    location: str = None


class TableUpdate(BaseModel):
    """Schema for updating table details"""
    table_number: str = None
    capacity: int = None
    location: str = None
    is_active: bool = None  # Set to False to take table out of service


class AvailabilityCheckRequest(BaseModel):
    """Request to check table availability"""
    restaurant_id: int
    party_size: int
    booking_date: str  # Format: YYYY-MM-DD
    booking_time: str  # Format: HH:MM


class AvailabilityResponse(BaseModel):
    """Response with availability information"""
    available: bool
    available_tables_count: int
    suggested_times: List[str] = []
    message: str


@router.post("/tables/", status_code=status.HTTP_201_CREATED)
async def create_table(
    table_data: TableCreate,
    db: SupabaseDB = Depends(get_db)
):
    """
    Create a new table for a restaurant.
    Restaurants can add tables manually through the dashboard.
    """
    # Verify restaurant exists
    restaurant = db.query_one("restaurants", {"id": table_data.restaurant_id})
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant {table_data.restaurant_id} not found"
        )

    # Check if table number already exists
    existing = db.query_one("tables", {
        "restaurant_id": table_data.restaurant_id,
        "table_number": table_data.table_number
    })

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Table {table_data.table_number} already exists"
        )

    # Create table
    table = db.insert("tables", {
        "restaurant_id": table_data.restaurant_id,
        "table_number": table_data.table_number,
        "capacity": table_data.capacity,
        "location": table_data.location,
        "is_active": True
    })

    return {
        "id": table["id"],
        "table_number": table["table_number"],
        "capacity": table["capacity"],
        "location": table["location"],
        "is_active": table["is_active"],
        "message": f"Table {table['table_number']} created successfully"
    }


@router.get("/tables/{restaurant_id}")
async def list_tables(
    restaurant_id: int,
    include_inactive: bool = False,
    db: SupabaseDB = Depends(get_db)
):
    """
    List all tables for a restaurant.
    Use include_inactive=true to see tables that are out of service.
    """
    query = db.table("tables").select("*").eq("restaurant_id", restaurant_id)

    if not include_inactive:
        query = query.eq("is_active", True)

    result = query.order("table_number").execute()
    tables = result.data or []

    return [{
        "id": t["id"],
        "table_number": t["table_number"],
        "capacity": t["capacity"],
        "location": t["location"],
        "is_active": t["is_active"]
    } for t in tables]


@router.patch("/tables/{table_id}")
async def update_table(
    table_id: int,
    updates: TableUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """
    Update table details or take table out of service.

    Examples:
    - Set is_active=false to take table out of service (maintenance, VIP reservation, etc.)
    - Update capacity if table configuration changes
    """
    table = db.query_one("tables", {"id": table_id})
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table {table_id} not found"
        )

    # Apply updates
    update_data = updates.model_dump(exclude_unset=True)

    if update_data:
        table = db.update("tables", table_id, update_data)

    status_msg = "out of service" if not table["is_active"] else "active"

    return {
        "id": table["id"],
        "table_number": table["table_number"],
        "capacity": table["capacity"],
        "is_active": table["is_active"],
        "message": f"Table {table['table_number']} is now {status_msg}"
    }


@router.post("/availability/check", response_model=AvailabilityResponse)
async def check_availability(
    request: AvailabilityCheckRequest,
    db: SupabaseDB = Depends(get_db)
):
    """
    Check table availability for a specific date/time and party size.
    Returns whether tables are available and suggests alternative times if not.
    """
    # Parse date and time
    booking_date = datetime.strptime(request.booking_date, "%Y-%m-%d")
    booking_time = datetime.strptime(request.booking_time, "%H:%M").time()

    # Find available table
    available_table = table_availability_service.find_available_table(
        db=db,
        restaurant_id=request.restaurant_id,
        party_size=request.party_size,
        booking_date=booking_date,
        booking_time=booking_time
    )

    if available_table:
        return AvailabilityResponse(
            available=True,
            available_tables_count=1,  # Could enhance to count all available
            message=f"Table available for {request.party_size} people at {request.booking_time}"
        )
    else:
        # Suggest alternative times
        alternatives = table_availability_service.suggest_alternative_times(
            db=db,
            restaurant_id=request.restaurant_id,
            party_size=request.party_size,
            booking_date=booking_date,
            requested_time=booking_time,
            max_suggestions=5
        )

        suggested_times = [t.strftime("%H:%M") for t in alternatives]

        return AvailabilityResponse(
            available=False,
            available_tables_count=0,
            suggested_times=suggested_times,
            message=f"No tables available for {request.party_size} at {request.booking_time}. Try: {', '.join([t.strftime('%I:%M %p') for t in alternatives[:3]])}" if alternatives else "No availability today"
        )


@router.get("/availability/slots/{restaurant_id}")
async def get_available_slots(
    restaurant_id: int,
    party_size: int,
    date: str,  # Format: YYYY-MM-DD
    db: SupabaseDB = Depends(get_db)
):
    """
    Get all available time slots for a specific date and party size.
    Useful for showing availability calendar in dashboard.
    """
    booking_date = datetime.strptime(date, "%Y-%m-%d")

    slots = table_availability_service.get_available_time_slots(
        db=db,
        restaurant_id=restaurant_id,
        party_size=party_size,
        booking_date=booking_date
    )

    return [{
        "time": t.strftime("%H:%M"),
        "time_formatted": t.strftime("%I:%M %p"),
        "available_tables": count
    } for t, count in slots]


@router.get("/tables/{table_id}/schedule")
async def get_table_schedule(
    table_id: int,
    date: str,  # Format: YYYY-MM-DD
    db: SupabaseDB = Depends(get_db)
):
    """
    Get the full booking schedule for a specific table on a specific date.
    Shows when table is booked and when it's free.
    """
    booking_date = datetime.strptime(date, "%Y-%m-%d")

    schedule = table_availability_service.get_table_schedule(
        db=db,
        table_id=table_id,
        date=booking_date
    )

    return {
        "table_id": table_id,
        "date": date,
        "bookings": schedule,
        "message": f"Found {len(schedule)} bookings for this table"
    }
