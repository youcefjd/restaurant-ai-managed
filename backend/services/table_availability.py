"""
Table Availability Service
Handles table availability checking, time slot conflicts, and automatic table assignment
"""

from datetime import datetime, timedelta, time as dt_time
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.models import Table, Booking, BookingStatus

# Standard reservation duration in minutes
DEFAULT_RESERVATION_DURATION = 90  # 90 minutes as requested


class TableAvailabilityService:
    """Service for managing table availability and bookings"""

    @staticmethod
    def find_available_table(
        db: Session,
        restaurant_id: int,
        party_size: int,
        booking_date,  # Can be date or datetime
        booking_time: dt_time,
        duration_minutes: int = DEFAULT_RESERVATION_DURATION
    ) -> Optional[Table]:
        """
        Find an available table for the given party size, date, and time.

        Returns the best matching table or None if no tables available.
        Priority: Smallest table that fits the party size.
        """
        # Get all active tables for this restaurant with sufficient capacity
        suitable_tables = db.query(Table).filter(
            Table.restaurant_id == restaurant_id,
            Table.capacity >= party_size,
            Table.is_active == True
        ).order_by(Table.capacity).all()  # Order by capacity (smallest first)

        if not suitable_tables:
            return None

        # Check each table for availability
        for table in suitable_tables:
            if TableAvailabilityService.is_table_available(
                db=db,
                table_id=table.id,
                booking_date=booking_date,
                booking_time=booking_time,
                duration_minutes=duration_minutes
            ):
                return table

        return None

    @staticmethod
    def is_table_available(
        db: Session,
        table_id: int,
        booking_date,  # Can be date or datetime
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

        # Get all bookings for this table on this date
        existing_bookings = db.query(Booking).filter(
            Booking.table_id == table_id,
            Booking.booking_date == the_date,
            Booking.status.in_(['pending', 'confirmed'])
        ).all()

        # Check for conflicts manually (SQLite doesn't support time arithmetic in queries)
        for existing in existing_bookings:
            existing_start = datetime.combine(the_date, existing.booking_time)
            existing_end = existing_start + timedelta(minutes=existing.duration_minutes)

            # Check if time ranges overlap
            if not (booking_end <= existing_start or booking_datetime >= existing_end):
                return False

        return True

    @staticmethod
    def get_available_time_slots(
        db: Session,
        restaurant_id: int,
        party_size: int,
        booking_date,  # Can be date or datetime
        start_hour: int = 17,  # 5 PM
        end_hour: int = 22,     # 10 PM
        slot_interval: int = 30  # Check every 30 minutes
    ) -> List[Tuple[dt_time, int]]:
        """
        Get all available time slots for a given party size and date.

        Returns list of (time, available_tables_count) tuples.
        """
        available_slots = []

        # Generate time slots
        current_time = dt_time(start_hour, 0)
        end_time = dt_time(end_hour, 0)

        while current_time < end_time:
            # Count available tables for this slot
            suitable_tables = db.query(Table).filter(
                Table.restaurant_id == restaurant_id,
                Table.capacity >= party_size,
                Table.is_active == True
            ).all()

            available_count = sum(
                1 for table in suitable_tables
                if TableAvailabilityService.is_table_available(
                    db=db,
                    table_id=table.id,
                    booking_date=booking_date,
                    booking_time=current_time,
                    duration_minutes=DEFAULT_RESERVATION_DURATION
                )
            )

            if available_count > 0:
                available_slots.append((current_time, available_count))

            # Move to next slot
            # Handle both date and datetime inputs
            the_date = booking_date.date() if hasattr(booking_date, 'date') else booking_date
            current_datetime = datetime.combine(the_date, current_time)
            next_datetime = current_datetime + timedelta(minutes=slot_interval)
            current_time = next_datetime.time()

        return available_slots

    @staticmethod
    def suggest_alternative_times(
        db: Session,
        restaurant_id: int,
        party_size: int,
        booking_date,  # Can be date or datetime
        requested_time: dt_time,
        max_suggestions: int = 3
    ) -> List[dt_time]:
        """
        Suggest alternative times near the requested time if original is not available.

        Returns list of available times closest to the requested time.
        """
        # Get all available slots for the day
        all_slots = TableAvailabilityService.get_available_time_slots(
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

        # Return up to max_suggestions times
        return [slot[0] for slot in sorted_slots[:max_suggestions]]

    @staticmethod
    def get_table_schedule(
        db: Session,
        table_id: int,
        schedule_date  # Can be date or datetime
    ) -> List[dict]:
        """
        Get the full schedule for a specific table on a specific date.

        Returns list of bookings with time slots.
        """
        # Handle both date and datetime inputs
        the_date = schedule_date.date() if hasattr(schedule_date, 'date') else schedule_date

        bookings = db.query(Booking).filter(
            Booking.table_id == table_id,
            Booking.booking_date == the_date,
            Booking.status.in_(['pending', 'confirmed'])
        ).order_by(Booking.booking_time).all()

        schedule = []
        for booking in bookings:
            booking_datetime = datetime.combine(the_date, booking.booking_time)
            end_time = booking_datetime + timedelta(minutes=booking.duration_minutes)

            schedule.append({
                'booking_id': booking.id,
                'start_time': booking.booking_time,
                'end_time': end_time.time(),
                'duration_minutes': booking.duration_minutes,
                'party_size': booking.party_size,
                'customer_id': booking.customer_id,
                'status': booking.status
            })

        return schedule


# Global service instance
table_availability_service = TableAvailabilityService()
