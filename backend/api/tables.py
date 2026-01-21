"""Table management endpoints with restaurant association."""

from typing import List
from datetime import date, time, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.database import get_db, SupabaseDB
from backend.schemas import TableCreate, TableUpdate, Table as TableResponse

router = APIRouter()


@router.post("/{restaurant_id}/tables", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
async def create_table(
    restaurant_id: int,
    table_data: TableCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new table for a restaurant."""
    # Verify restaurant exists
    restaurant = db.query_one("restaurants", {"id": restaurant_id})
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant {restaurant_id} not found"
        )

    # Check for duplicate table number
    existing = db.table("tables").select("*").eq(
        "restaurant_id", restaurant_id
    ).eq("table_number", table_data.table_number).execute()

    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Table {table_data.table_number} already exists"
        )

    # Override restaurant_id from path parameter
    table_dict = table_data.model_dump()
    table_dict['restaurant_id'] = restaurant_id

    table = db.insert("tables", table_dict)
    return table


@router.get("/{restaurant_id}/tables/{table_id}", response_model=TableResponse)
async def get_table(restaurant_id: int, table_id: int, db: SupabaseDB = Depends(get_db)):
    """Get a table by ID."""
    result = db.table("tables").select("*").eq(
        "id", table_id
    ).eq("restaurant_id", restaurant_id).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )
    return result.data[0]


@router.get("/{restaurant_id}/tables", response_model=List[TableResponse])
async def list_tables(
    restaurant_id: int,
    skip: int = 0,
    limit: int = 100,
    db: SupabaseDB = Depends(get_db)
):
    """List all tables for a restaurant."""
    result = db.table("tables").select("*").eq(
        "restaurant_id", restaurant_id
    ).range(skip, skip + limit - 1).execute()

    return result.data or []


@router.put("/{restaurant_id}/tables/{table_id}", response_model=TableResponse)
async def update_table(
    restaurant_id: int,
    table_id: int,
    table_data: TableUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """Update a table."""
    # Check if table exists
    existing = db.table("tables").select("*").eq(
        "id", table_id
    ).eq("restaurant_id", restaurant_id).execute()

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )

    update_data = table_data.model_dump(exclude_unset=True)
    if update_data:
        table = db.update("tables", table_id, update_data)
    else:
        table = existing.data[0]

    return table


@router.delete("/{restaurant_id}/tables/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(restaurant_id: int, table_id: int, db: SupabaseDB = Depends(get_db)):
    """Delete a table."""
    # Check if table exists
    existing = db.table("tables").select("*").eq(
        "id", table_id
    ).eq("restaurant_id", restaurant_id).execute()

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )

    db.delete("tables", table_id)
    return None


@router.get("/{restaurant_id}/tables/availability/count")
async def get_available_tables_count(
    restaurant_id: int,
    booking_date: date = Query(..., description="Date to check availability (YYYY-MM-DD)"),
    booking_time: time = Query(..., description="Time to check availability (HH:MM:SS)"),
    party_size: int = Query(..., ge=1, description="Party size"),
    db: SupabaseDB = Depends(get_db)
):
    """
    Get count of available tables for a specific date, time, and party size.

    Returns:
        - total_tables: Total number of active tables at this restaurant
        - available_tables: Number of tables available for this time slot
        - party_size_compatible: Number of tables that can accommodate party size
        - tables_available: List of available table numbers
    """
    # Get all active tables
    all_tables_result = db.table("tables").select("*").eq(
        "restaurant_id", restaurant_id
    ).eq("is_active", True).execute()

    all_tables = all_tables_result.data or []
    total_tables = len(all_tables)

    # Filter tables that can accommodate party size
    compatible_tables = [t for t in all_tables if t["capacity"] >= party_size]

    # Check which tables are available at this time
    available_tables = []
    start_datetime = datetime.combine(booking_date, booking_time)
    end_datetime = start_datetime + timedelta(minutes=120)  # 2 hour booking

    for table in compatible_tables:
        # Check for conflicts
        conflicts_result = db.table("bookings").select("*").eq(
            "table_id", table["id"]
        ).eq("booking_date", str(booking_date)).in_(
            "status", ["confirmed", "pending"]
        ).execute()

        conflicts = conflicts_result.data or []

        has_conflict = False
        for conflict in conflicts:
            conflict_time = datetime.strptime(conflict["booking_time"], "%H:%M:%S").time()
            conflict_start = datetime.combine(booking_date, conflict_time)
            conflict_end = conflict_start + timedelta(minutes=conflict["duration_minutes"])

            # Check time overlap
            if not (end_datetime <= conflict_start or start_datetime >= conflict_end):
                has_conflict = True
                break

        if not has_conflict:
            available_tables.append({
                "table_id": table["id"],
                "table_number": table["table_number"],
                "capacity": table["capacity"],
                "location": table["location"]
            })

    return {
        "restaurant_id": restaurant_id,
        "booking_date": booking_date,
        "booking_time": booking_time,
        "party_size": party_size,
        "total_tables": total_tables,
        "party_size_compatible_tables": len(compatible_tables),
        "available_tables_count": len(available_tables),
        "available_tables": available_tables
    }
