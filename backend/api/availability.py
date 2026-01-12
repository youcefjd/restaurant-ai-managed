"""Availability checking endpoint with conflict detection."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Table, Booking, BookingStatus
from backend.schemas import AvailabilityQuery, AvailabilityResponse, TimeSlot

router = APIRouter()


@router.post("/check", response_model=AvailabilityResponse)
async def check_availability(
    query: AvailabilityQuery,
    db: Session = Depends(get_db)
):
    """Check table availability for given date, time, and party size."""

    # Get all active tables for the restaurant
    tables = db.query(Table).filter(
        Table.restaurant_id == query.restaurant_id,
        Table.is_active == True,
        Table.capacity >= query.party_size
    ).all()

    if not tables:
        return AvailabilityResponse(
            requested_time=query.requested_time,
            is_available=False,
            available_tables=[],
            alternative_times=[],
            message="No tables available for this party size"
        )

    # Check for conflicts
    duration = query.duration_minutes or 120
    requested_start = datetime.combine(query.requested_date, query.requested_time)
    requested_end = requested_start + timedelta(minutes=duration)

    available_tables = []
    for table in tables:
        # Check if table has conflicting bookings
        conflicts = db.query(Booking).filter(
            Booking.table_id == table.id,
            Booking.booking_date == query.requested_date,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        ).all()

        has_conflict = False
        for booking in conflicts:
            booking_start = datetime.combine(booking.booking_date, booking.booking_time)
            booking_end = booking_start + timedelta(minutes=booking.duration_minutes)

            # Check for time overlap
            if not (requested_end <= booking_start or requested_start >= booking_end):
                has_conflict = True
                break

        if not has_conflict:
            available_tables.append(table)

    return AvailabilityResponse(
        requested_time=query.requested_time,
        is_available=len(available_tables) > 0,
        available_tables=available_tables,
        alternative_times=[],  # TODO: Implement alternative time suggestions
        message=f"Found {len(available_tables)} available table(s)" if available_tables else "No tables available at requested time"
    )
