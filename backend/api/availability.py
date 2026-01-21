"""Availability checking endpoint with conflict detection."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status

from backend.database import get_db, SupabaseDB
from backend.schemas import AvailabilityQuery, AvailabilityResponse, TimeSlot, Table as TableSchema

router = APIRouter()


@router.post("/check", response_model=AvailabilityResponse)
async def check_availability(
    query: AvailabilityQuery,
    db: SupabaseDB = Depends(get_db)
):
    """Check table availability for given date, time, and party size."""

    # Get all active tables for the restaurant with sufficient capacity
    tables_result = db.table("tables").select("*").eq(
        "restaurant_id", query.restaurant_id
    ).eq(
        "is_active", True
    ).gte(
        "capacity", query.party_size
    ).execute()

    tables = tables_result.data or []

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
        # Get bookings for this table on the requested date with pending or confirmed status
        bookings_result = db.table("bookings").select("*").eq(
            "table_id", table["id"]
        ).eq(
            "booking_date", query.requested_date.isoformat()
        ).in_(
            "status", ["pending", "confirmed"]
        ).execute()

        conflicts = bookings_result.data or []

        has_conflict = False
        for booking in conflicts:
            # Parse booking time - handle both string and time formats
            booking_time = booking["booking_time"]
            if isinstance(booking_time, str):
                # Parse time string (format: "HH:MM:SS" or "HH:MM")
                time_parts = booking_time.split(":")
                booking_time_obj = datetime.strptime(booking_time[:8], "%H:%M:%S").time() if len(time_parts) == 3 else datetime.strptime(booking_time[:5], "%H:%M").time()
            else:
                booking_time_obj = booking_time

            booking_date = booking["booking_date"]
            if isinstance(booking_date, str):
                booking_date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
            else:
                booking_date_obj = booking_date

            booking_start = datetime.combine(booking_date_obj, booking_time_obj)
            booking_end = booking_start + timedelta(minutes=booking["duration_minutes"])

            # Check for time overlap
            if not (requested_end <= booking_start or requested_start >= booking_end):
                has_conflict = True
                break

        if not has_conflict:
            # Convert dict to TableSchema for response
            available_tables.append(TableSchema(
                id=table["id"],
                restaurant_id=table["restaurant_id"],
                table_number=table["table_number"],
                capacity=table["capacity"],
                location=table.get("location"),
                is_active=table["is_active"],
                created_at=table["created_at"]
            ))

    return AvailabilityResponse(
        requested_time=query.requested_time,
        is_available=len(available_tables) > 0,
        available_tables=available_tables,
        alternative_times=[],  # TODO: Implement alternative time suggestions
        message=f"Found {len(available_tables)} available table(s)" if available_tables else "No tables available at requested time"
    )
