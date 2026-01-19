"""Table management endpoints with restaurant association."""

from typing import List
from datetime import date, time, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Table, Booking, BookingStatus, Restaurant
from backend.schemas import TableCreate, TableUpdate, Table as TableResponse

router = APIRouter()


@router.post("/{restaurant_id}/tables", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
async def create_table(
    restaurant_id: int,
    table_data: TableCreate,
    db: Session = Depends(get_db)
):
    """Create a new table for a restaurant."""
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant {restaurant_id} not found"
        )

    # Check for duplicate table number
    existing = db.query(Table).filter(
        Table.restaurant_id == restaurant_id,
        Table.table_number == table_data.table_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Table {table_data.table_number} already exists"
        )

    # Override restaurant_id from path parameter
    table_dict = table_data.model_dump()
    table_dict['restaurant_id'] = restaurant_id

    table = Table(**table_dict)
    db.add(table)
    db.commit()
    db.refresh(table)
    return table


@router.get("/{restaurant_id}/tables/{table_id}", response_model=TableResponse)
async def get_table(restaurant_id: int, table_id: int, db: Session = Depends(get_db)):
    """Get a table by ID."""
    table = db.query(Table).filter(
        Table.id == table_id,
        Table.restaurant_id == restaurant_id
    ).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )
    return table


@router.get("/{restaurant_id}/tables", response_model=List[TableResponse])
async def list_tables(
    restaurant_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all tables for a restaurant."""
    tables = db.query(Table).filter(
        Table.restaurant_id == restaurant_id
    ).offset(skip).limit(limit).all()
    return tables


@router.put("/{restaurant_id}/tables/{table_id}", response_model=TableResponse)
async def update_table(
    restaurant_id: int,
    table_id: int,
    table_data: TableUpdate,
    db: Session = Depends(get_db)
):
    """Update a table."""
    table = db.query(Table).filter(
        Table.id == table_id,
        Table.restaurant_id == restaurant_id
    ).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )

    update_data = table_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(table, field, value)

    db.commit()
    db.refresh(table)
    return table


@router.delete("/{restaurant_id}/tables/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(restaurant_id: int, table_id: int, db: Session = Depends(get_db)):
    """Delete a table."""
    table = db.query(Table).filter(
        Table.id == table_id,
        Table.restaurant_id == restaurant_id
    ).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )

    db.delete(table)
    db.commit()
    return None


@router.get("/{restaurant_id}/tables/availability/count")
async def get_available_tables_count(
    restaurant_id: int,
    booking_date: date = Query(..., description="Date to check availability (YYYY-MM-DD)"),
    booking_time: time = Query(..., description="Time to check availability (HH:MM:SS)"),
    party_size: int = Query(..., ge=1, description="Party size"),
    db: Session = Depends(get_db)
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
    all_tables = db.query(Table).filter(
        Table.restaurant_id == restaurant_id,
        Table.is_active == True
    ).all()

    total_tables = len(all_tables)

    # Filter tables that can accommodate party size
    compatible_tables = [t for t in all_tables if t.capacity >= party_size]

    # Check which tables are available at this time
    available_tables = []
    start_datetime = datetime.combine(booking_date, booking_time)
    end_datetime = start_datetime + timedelta(minutes=120)  # 2 hour booking

    for table in compatible_tables:
        # Check for conflicts
        conflicts = db.query(Booking).filter(
            Booking.table_id == table.id,
            Booking.booking_date == booking_date,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
        ).all()

        has_conflict = False
        for conflict in conflicts:
            conflict_start = datetime.combine(booking_date, conflict.booking_time)
            conflict_end = conflict_start + timedelta(minutes=conflict.duration_minutes)

            # Check time overlap
            if not (end_datetime <= conflict_start or start_datetime >= conflict_end):
                has_conflict = True
                break

        if not has_conflict:
            available_tables.append({
                "table_id": table.id,
                "table_number": table.table_number,
                "capacity": table.capacity,
                "location": table.location
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
