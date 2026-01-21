"""Booking CRUD endpoints with status management."""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta, time as dt_time

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.database import get_db, SupabaseDB
from backend.schemas import BookingCreate, BookingUpdate, Booking as BookingResponse
from backend.services.sms_service import sms_service

router = APIRouter()

# Standard reservation duration in minutes
DEFAULT_RESERVATION_DURATION = 90


def find_available_table(
    db: SupabaseDB,
    restaurant_id: int,
    party_size: int,
    booking_date,
    booking_time: dt_time,
    duration_minutes: int = DEFAULT_RESERVATION_DURATION
) -> Optional[Dict[str, Any]]:
    """
    Find an available table for the given party size, date, and time.
    Returns the best matching table dict or None if no tables available.
    """
    # Get all active tables for this restaurant with sufficient capacity
    result = db.table("tables").select("*").eq(
        "restaurant_id", restaurant_id
    ).gte("capacity", party_size).eq("is_active", True).order("capacity").execute()

    suitable_tables = result.data or []

    if not suitable_tables:
        return None

    # Check each table for availability
    for table in suitable_tables:
        if is_table_available(
            db=db,
            table_id=table["id"],
            booking_date=booking_date,
            booking_time=booking_time,
            duration_minutes=duration_minutes
        ):
            return table

    return None


def is_table_available(
    db: SupabaseDB,
    table_id: int,
    booking_date,
    booking_time: dt_time,
    duration_minutes: int = DEFAULT_RESERVATION_DURATION
) -> bool:
    """
    Check if a specific table is available for the given date and time.
    Returns True if table is free, False if there's a conflict.
    """
    # Handle both date and datetime inputs
    if hasattr(booking_date, 'date'):
        the_date = booking_date.date()
    else:
        the_date = booking_date

    # Convert booking_time to datetime for comparison
    booking_datetime = datetime.combine(the_date, booking_time)
    booking_end = booking_datetime + timedelta(minutes=duration_minutes)

    # Get all bookings for this table on this date with pending or confirmed status
    result = db.table("bookings").select("*").eq(
        "table_id", table_id
    ).eq("booking_date", str(the_date)).in_(
        "status", ["pending", "confirmed"]
    ).execute()

    existing_bookings = result.data or []

    # Check for conflicts
    for existing in existing_bookings:
        # Parse the booking_time from string if needed
        existing_time = existing["booking_time"]
        if isinstance(existing_time, str):
            existing_time = dt_time.fromisoformat(existing_time)

        existing_start = datetime.combine(the_date, existing_time)
        existing_end = existing_start + timedelta(minutes=existing["duration_minutes"])

        # Check if time ranges overlap
        if not (booking_end <= existing_start or booking_datetime >= existing_end):
            return False

    return True


def get_available_time_slots(
    db: SupabaseDB,
    restaurant_id: int,
    party_size: int,
    booking_date,
    start_hour: int = 17,
    end_hour: int = 22,
    slot_interval: int = 30
) -> List[tuple]:
    """
    Get all available time slots for a given party size and date.
    Returns list of (time, available_tables_count) tuples.
    """
    available_slots = []

    # Generate time slots
    current_time = dt_time(start_hour, 0)
    end_time = dt_time(end_hour, 0)

    # Get all suitable tables
    result = db.table("tables").select("*").eq(
        "restaurant_id", restaurant_id
    ).gte("capacity", party_size).eq("is_active", True).execute()

    suitable_tables = result.data or []

    while current_time < end_time:
        available_count = sum(
            1 for table in suitable_tables
            if is_table_available(
                db=db,
                table_id=table["id"],
                booking_date=booking_date,
                booking_time=current_time,
                duration_minutes=DEFAULT_RESERVATION_DURATION
            )
        )

        if available_count > 0:
            available_slots.append((current_time, available_count))

        # Move to next slot
        the_date = booking_date.date() if hasattr(booking_date, 'date') else booking_date
        current_datetime = datetime.combine(the_date, current_time)
        next_datetime = current_datetime + timedelta(minutes=slot_interval)
        current_time = next_datetime.time()

    return available_slots


def suggest_alternative_times(
    db: SupabaseDB,
    restaurant_id: int,
    party_size: int,
    booking_date,
    requested_time: dt_time,
    max_suggestions: int = 3
) -> List[dt_time]:
    """
    Suggest alternative times near the requested time if original is not available.
    Returns list of available times closest to the requested time.
    """
    all_slots = get_available_time_slots(
        db=db,
        restaurant_id=restaurant_id,
        party_size=party_size,
        booking_date=booking_date
    )

    if not all_slots:
        return []

    # Convert requested time to minutes since midnight for comparison
    requested_minutes = requested_time.hour * 60 + requested_time.minute

    # Sort slots by distance from requested time
    sorted_slots = sorted(
        all_slots,
        key=lambda x: abs((x[0].hour * 60 + x[0].minute) - requested_minutes)
    )

    return [slot[0] for slot in sorted_slots[:max_suggestions]]


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new booking."""
    # Get or create customer
    customer = db.query_one("customers", {"phone": booking_data.customer_phone})

    if not customer:
        if not booking_data.customer_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer name required for new customers"
            )
        customer = db.insert("customers", {
            "phone": booking_data.customer_phone,
            "name": booking_data.customer_name,
            "email": booking_data.customer_email
        })

    # Find available table using availability service
    available_table = find_available_table(
        db=db,
        restaurant_id=booking_data.restaurant_id,
        party_size=booking_data.party_size,
        booking_date=booking_data.booking_date,
        booking_time=booking_data.booking_time,
        duration_minutes=booking_data.duration_minutes or DEFAULT_RESERVATION_DURATION
    )

    if not available_table:
        # No tables available - suggest alternative times
        alternatives = suggest_alternative_times(
            db=db,
            restaurant_id=booking_data.restaurant_id,
            party_size=booking_data.party_size,
            booking_date=booking_data.booking_date,
            requested_time=booking_data.booking_time
        )

        alt_times_str = ", ".join([t.strftime("%I:%M %p") for t in alternatives[:3]])
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No tables available for {booking_data.party_size} people at {booking_data.booking_time.strftime('%I:%M %p')}. " +
                   (f"Try these times: {alt_times_str}" if alternatives else "No availability today.")
        )

    # Create booking with assigned table
    booking_dict = booking_data.model_dump(exclude={'customer_phone', 'customer_name', 'customer_email', 'duration_minutes'})

    # Convert date and time to string format for Supabase
    booking_dict["booking_date"] = str(booking_dict["booking_date"])
    booking_dict["booking_time"] = str(booking_dict["booking_time"])

    booking = db.insert("bookings", {
        **booking_dict,
        "customer_id": customer["id"],
        "table_id": available_table["id"],
        "duration_minutes": booking_data.duration_minutes or DEFAULT_RESERVATION_DURATION,
        "status": "confirmed"
    })

    # Send SMS confirmation
    try:
        restaurant = db.query_one("restaurants", {"id": booking["restaurant_id"]})
        if restaurant:
            sms_service.send_booking_confirmation(booking, customer, restaurant)
    except Exception as e:
        # Log but don't fail the booking if SMS fails
        print(f"SMS sending failed: {e}")

    return booking


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, db: SupabaseDB = Depends(get_db)):
    """Get a booking by ID."""
    booking = db.query_one("bookings", {"id": booking_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    return booking


@router.get("/", response_model=List[BookingResponse])
async def list_bookings(
    restaurant_id: int = Query(None),
    account_id: int = Query(None),
    status_filter: str = Query(None),
    date_from: date = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: SupabaseDB = Depends(get_db)
):
    """List bookings with optional filters."""
    query = db.table("bookings").select("*")

    if restaurant_id:
        query = query.eq("restaurant_id", restaurant_id)
    elif account_id:
        # Filter by account_id - find all restaurants for this account
        restaurants_result = db.table("restaurants").select("id").eq("account_id", account_id).execute()
        restaurant_ids = [r["id"] for r in (restaurants_result.data or [])]
        if restaurant_ids:
            query = query.in_("restaurant_id", restaurant_ids)
        else:
            # No restaurants for this account, return empty
            return []

    if status_filter:
        query = query.eq("status", status_filter)
    if date_from:
        query = query.gte("booking_date", str(date_from))

    # Order by booking_date desc, then booking_time desc
    query = query.order("booking_date", desc=True).order("booking_time", desc=True)

    # Apply pagination
    query = query.range(skip, skip + limit - 1)

    result = query.execute()
    return result.data or []


@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    booking_data: BookingUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """Update a booking."""
    booking = db.query_one("bookings", {"id": booking_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    update_data = booking_data.model_dump(exclude_unset=True)

    # Convert date and time to string format if present
    if "booking_date" in update_data and update_data["booking_date"]:
        update_data["booking_date"] = str(update_data["booking_date"])
    if "booking_time" in update_data and update_data["booking_time"]:
        update_data["booking_time"] = str(update_data["booking_time"])

    updated_booking = db.update("bookings", booking_id, update_data)
    return updated_booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(booking_id: int, db: SupabaseDB = Depends(get_db)):
    """Cancel a booking."""
    booking = db.query_one("bookings", {"id": booking_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Send cancellation SMS before updating status
    try:
        customer = db.query_one("customers", {"id": booking["customer_id"]})
        restaurant = db.query_one("restaurants", {"id": booking["restaurant_id"]})
        if customer and restaurant:
            sms_service.send_cancellation_confirmation(booking, customer, restaurant)
    except Exception as e:
        print(f"SMS sending failed: {e}")

    db.update("bookings", booking_id, {"status": "cancelled"})
    return None
