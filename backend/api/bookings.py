"""Booking CRUD endpoints with status management."""

from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Booking, Customer, BookingStatus, Restaurant
from backend.schemas import BookingCreate, BookingUpdate, Booking as BookingResponse
from backend.services.sms_service import sms_service

router = APIRouter()


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db)
):
    """Create a new booking."""
    # Get or create customer
    customer = db.query(Customer).filter(Customer.phone == booking_data.customer_phone).first()
    if not customer:
        if not booking_data.customer_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer name required for new customers"
            )
        customer = Customer(
            phone=booking_data.customer_phone,
            name=booking_data.customer_name,
            email=booking_data.customer_email
        )
        db.add(customer)
        db.flush()

    # Create booking (simplified - no table assignment yet)
    booking_dict = booking_data.model_dump(exclude={'customer_phone', 'customer_name', 'customer_email', 'duration_minutes'})
    booking = Booking(
        **booking_dict,
        customer_id=customer.id,
        table_id=1,  # TODO: Implement automatic table assignment
        duration_minutes=booking_data.duration_minutes or 120,
        status=BookingStatus.CONFIRMED  # Auto-confirm
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Send SMS confirmation
    try:
        restaurant = db.query(Restaurant).filter(Restaurant.id == booking.restaurant_id).first()
        if restaurant:
            sms_service.send_booking_confirmation(booking, customer, restaurant)
    except Exception as e:
        # Log but don't fail the booking if SMS fails
        print(f"SMS sending failed: {e}")

    return booking


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """Get a booking by ID."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
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
    db: Session = Depends(get_db)
):
    """List bookings with optional filters."""
    query = db.query(Booking)

    if restaurant_id:
        query = query.filter(Booking.restaurant_id == restaurant_id)
    elif account_id:
        # Filter by account_id - find all restaurants for this account
        restaurant_ids = db.query(Restaurant.id).filter(Restaurant.account_id == account_id).all()
        restaurant_ids = [r[0] for r in restaurant_ids]
        if restaurant_ids:
            query = query.filter(Booking.restaurant_id.in_(restaurant_ids))
        else:
            # No restaurants for this account, return empty
            return []

    if status_filter:
        query = query.filter(Booking.status == status_filter)
    if date_from:
        query = query.filter(Booking.booking_date >= date_from)

    bookings = query.order_by(Booking.booking_date.desc(), Booking.booking_time.desc()).offset(skip).limit(limit).all()
    return bookings


@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    booking_data: BookingUpdate,
    db: Session = Depends(get_db)
):
    """Update a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    update_data = booking_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)

    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    """Cancel a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Send cancellation SMS before updating status
    try:
        customer = db.query(Customer).filter(Customer.id == booking.customer_id).first()
        restaurant = db.query(Restaurant).filter(Restaurant.id == booking.restaurant_id).first()
        if customer and restaurant:
            sms_service.send_cancellation_confirmation(booking, customer, restaurant)
    except Exception as e:
        print(f"SMS sending failed: {e}")

    booking.status = BookingStatus.CANCELLED
    db.commit()
    return None
