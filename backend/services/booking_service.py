"""
Booking Service - Core booking logic using Supabase.

Purpose: Core booking logic including availability checking and table assignment algorithms
File: backend/services/booking_service.py
"""

from datetime import datetime, timedelta, time as dt_time, date
from typing import List, Optional, Dict, Any, Tuple

from backend.database import SupabaseDB, get_db_context


# Standard reservation duration in minutes
DEFAULT_RESERVATION_DURATION = 90


class BookingService:
    """Service for managing bookings with Supabase backend."""

    def __init__(self, db: Optional[SupabaseDB] = None):
        """Initialize booking service with optional database instance."""
        self._db = db

    def _get_db(self) -> SupabaseDB:
        """Get database instance, creating one if not provided."""
        if self._db is None:
            self._db = SupabaseDB()
        return self._db

    def find_available_table(
        self,
        db: SupabaseDB,
        restaurant_id: int,
        party_size: int,
        booking_date: date,
        booking_time: dt_time,
        duration_minutes: int = DEFAULT_RESERVATION_DURATION
    ) -> Optional[Dict[str, Any]]:
        """
        Find an available table for the given party size, date, and time.

        Args:
            db: SupabaseDB instance
            restaurant_id: Restaurant ID
            party_size: Number of guests
            booking_date: Date of booking
            booking_time: Time of booking
            duration_minutes: Duration of reservation

        Returns:
            Dict representing the table or None if no tables available.
            Priority: Smallest table that fits the party size.
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
            if self.is_table_available(
                db=db,
                table_id=table["id"],
                booking_date=booking_date,
                booking_time=booking_time,
                duration_minutes=duration_minutes
            ):
                return table

        return None

    def is_table_available(
        self,
        db: SupabaseDB,
        table_id: int,
        booking_date: date,
        booking_time: dt_time,
        duration_minutes: int = DEFAULT_RESERVATION_DURATION,
        exclude_booking_id: Optional[int] = None
    ) -> bool:
        """
        Check if a specific table is available for the given date and time.

        Args:
            db: SupabaseDB instance
            table_id: Table ID to check
            booking_date: Date of booking
            booking_time: Time of booking
            duration_minutes: Duration of reservation
            exclude_booking_id: Optional booking ID to exclude (for updates)

        Returns:
            True if table is free, False if there's a conflict.
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
        query = db.table("bookings").select("*").eq(
            "table_id", table_id
        ).eq("booking_date", str(the_date)).in_(
            "status", ["pending", "confirmed"]
        )

        result = query.execute()
        existing_bookings = result.data or []

        # Check for conflicts
        for existing in existing_bookings:
            # Skip the booking being updated
            if exclude_booking_id and existing["id"] == exclude_booking_id:
                continue

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
        self,
        db: SupabaseDB,
        restaurant_id: int,
        party_size: int,
        booking_date: date,
        start_hour: int = 17,
        end_hour: int = 22,
        slot_interval: int = 30
    ) -> List[Tuple[dt_time, int]]:
        """
        Get all available time slots for a given party size and date.

        Args:
            db: SupabaseDB instance
            restaurant_id: Restaurant ID
            party_size: Number of guests
            booking_date: Date to check
            start_hour: Start hour for availability (default 5 PM)
            end_hour: End hour for availability (default 10 PM)
            slot_interval: Minutes between slots (default 30)

        Returns:
            List of (time, available_tables_count) tuples.
        """
        available_slots = []

        # Generate time slots
        current_time = dt_time(start_hour, 0)
        end_time = dt_time(end_hour, 0)

        # Get all suitable tables once
        result = db.table("tables").select("*").eq(
            "restaurant_id", restaurant_id
        ).gte("capacity", party_size).eq("is_active", True).execute()

        suitable_tables = result.data or []

        # Handle both date and datetime inputs
        the_date = booking_date.date() if hasattr(booking_date, 'date') else booking_date

        while current_time < end_time:
            available_count = sum(
                1 for table in suitable_tables
                if self.is_table_available(
                    db=db,
                    table_id=table["id"],
                    booking_date=the_date,
                    booking_time=current_time,
                    duration_minutes=DEFAULT_RESERVATION_DURATION
                )
            )

            if available_count > 0:
                available_slots.append((current_time, available_count))

            # Move to next slot
            current_datetime = datetime.combine(the_date, current_time)
            next_datetime = current_datetime + timedelta(minutes=slot_interval)
            current_time = next_datetime.time()

        return available_slots

    def suggest_alternative_times(
        self,
        db: SupabaseDB,
        restaurant_id: int,
        party_size: int,
        booking_date: date,
        requested_time: dt_time,
        max_suggestions: int = 3
    ) -> List[dt_time]:
        """
        Suggest alternative times near the requested time if original is not available.

        Args:
            db: SupabaseDB instance
            restaurant_id: Restaurant ID
            party_size: Number of guests
            booking_date: Date to check
            requested_time: Originally requested time
            max_suggestions: Maximum number of alternatives to return

        Returns:
            List of available times closest to the requested time.
        """
        all_slots = self.get_available_time_slots(
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

    def get_table_schedule(
        self,
        db: SupabaseDB,
        table_id: int,
        schedule_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get the full schedule for a specific table on a specific date.

        Args:
            db: SupabaseDB instance
            table_id: Table ID
            schedule_date: Date to get schedule for

        Returns:
            List of booking dicts with time slots.
        """
        # Handle both date and datetime inputs
        the_date = schedule_date.date() if hasattr(schedule_date, 'date') else schedule_date

        result = db.table("bookings").select("*").eq(
            "table_id", table_id
        ).eq("booking_date", str(the_date)).in_(
            "status", ["pending", "confirmed"]
        ).order("booking_time").execute()

        bookings = result.data or []

        schedule = []
        for booking in bookings:
            booking_time = booking["booking_time"]
            if isinstance(booking_time, str):
                booking_time = dt_time.fromisoformat(booking_time)

            booking_datetime = datetime.combine(the_date, booking_time)
            end_time = booking_datetime + timedelta(minutes=booking["duration_minutes"])

            schedule.append({
                'booking_id': booking["id"],
                'start_time': booking_time,
                'end_time': end_time.time(),
                'duration_minutes': booking["duration_minutes"],
                'party_size': booking["party_size"],
                'customer_id': booking["customer_id"],
                'status': booking["status"]
            })

        return schedule

    def create_booking(
        self,
        db: SupabaseDB,
        restaurant_id: int,
        customer_id: int,
        party_size: int,
        booking_date: date,
        booking_time: dt_time,
        duration_minutes: int = DEFAULT_RESERVATION_DURATION,
        special_requests: Optional[str] = None,
        table_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new booking with automatic table assignment.

        Args:
            db: SupabaseDB instance
            restaurant_id: Restaurant ID
            customer_id: Customer ID
            party_size: Number of guests
            booking_date: Date of booking
            booking_time: Time of booking
            duration_minutes: Duration of reservation
            special_requests: Optional special requests
            table_id: Optional specific table ID (auto-assigned if not provided)

        Returns:
            Created booking dict

        Raises:
            ValueError: If no tables available
        """
        # Find or validate table
        if table_id:
            # Verify specified table is available
            if not self.is_table_available(
                db=db,
                table_id=table_id,
                booking_date=booking_date,
                booking_time=booking_time,
                duration_minutes=duration_minutes
            ):
                raise ValueError(f"Table {table_id} is not available at the requested time")
            assigned_table_id = table_id
        else:
            # Auto-assign table
            available_table = self.find_available_table(
                db=db,
                restaurant_id=restaurant_id,
                party_size=party_size,
                booking_date=booking_date,
                booking_time=booking_time,
                duration_minutes=duration_minutes
            )

            if not available_table:
                raise ValueError("No tables available for the requested time and party size")

            assigned_table_id = available_table["id"]

        # Create booking
        booking_data = {
            "restaurant_id": restaurant_id,
            "customer_id": customer_id,
            "table_id": assigned_table_id,
            "party_size": party_size,
            "booking_date": str(booking_date),
            "booking_time": str(booking_time),
            "duration_minutes": duration_minutes,
            "status": "confirmed"
        }

        if special_requests:
            booking_data["special_requests"] = special_requests

        booking = db.insert("bookings", booking_data)
        return booking

    def update_booking(
        self,
        db: SupabaseDB,
        booking_id: int,
        party_size: Optional[int] = None,
        booking_date: Optional[date] = None,
        booking_time: Optional[dt_time] = None,
        duration_minutes: Optional[int] = None,
        special_requests: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing booking.

        Args:
            db: SupabaseDB instance
            booking_id: Booking ID to update
            party_size: New party size
            booking_date: New date
            booking_time: New time
            duration_minutes: New duration
            special_requests: New special requests
            status: New status

        Returns:
            Updated booking dict

        Raises:
            ValueError: If booking not found or update conflicts with availability
        """
        # Get existing booking
        booking = db.query_one("bookings", {"id": booking_id})
        if not booking:
            raise ValueError(f"Booking {booking_id} not found")

        update_data = {}

        # Check if time/date/size changes require table reassignment
        needs_availability_check = any([party_size, booking_date, booking_time, duration_minutes])

        if needs_availability_check:
            # Use existing values for unchanged fields
            check_party_size = party_size or booking["party_size"]
            check_date = booking_date or (
                datetime.strptime(booking["booking_date"], "%Y-%m-%d").date()
                if isinstance(booking["booking_date"], str)
                else booking["booking_date"]
            )
            check_time = booking_time or (
                dt_time.fromisoformat(booking["booking_time"])
                if isinstance(booking["booking_time"], str)
                else booking["booking_time"]
            )
            check_duration = duration_minutes or booking["duration_minutes"]

            # Check if current table still works
            if not self.is_table_available(
                db=db,
                table_id=booking["table_id"],
                booking_date=check_date,
                booking_time=check_time,
                duration_minutes=check_duration,
                exclude_booking_id=booking_id
            ):
                # Try to find a new table
                new_table = self.find_available_table(
                    db=db,
                    restaurant_id=booking["restaurant_id"],
                    party_size=check_party_size,
                    booking_date=check_date,
                    booking_time=check_time,
                    duration_minutes=check_duration
                )

                if not new_table:
                    raise ValueError("No tables available for the updated time and party size")

                update_data["table_id"] = new_table["id"]

        # Build update data
        if party_size:
            update_data["party_size"] = party_size
        if booking_date:
            update_data["booking_date"] = str(booking_date)
        if booking_time:
            update_data["booking_time"] = str(booking_time)
        if duration_minutes:
            update_data["duration_minutes"] = duration_minutes
        if special_requests is not None:
            update_data["special_requests"] = special_requests
        if status:
            update_data["status"] = status

        if not update_data:
            return booking

        updated_booking = db.update("bookings", booking_id, update_data)
        return updated_booking

    def cancel_booking(
        self,
        db: SupabaseDB,
        booking_id: int
    ) -> Dict[str, Any]:
        """
        Cancel a booking.

        Args:
            db: SupabaseDB instance
            booking_id: Booking ID to cancel

        Returns:
            Updated booking dict

        Raises:
            ValueError: If booking not found
        """
        booking = db.query_one("bookings", {"id": booking_id})
        if not booking:
            raise ValueError(f"Booking {booking_id} not found")

        updated_booking = db.update("bookings", booking_id, {"status": "cancelled"})
        return updated_booking

    def get_booking(
        self,
        db: SupabaseDB,
        booking_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a booking by ID.

        Args:
            db: SupabaseDB instance
            booking_id: Booking ID

        Returns:
            Booking dict or None
        """
        return db.query_one("bookings", {"id": booking_id})

    def get_bookings_for_restaurant(
        self,
        db: SupabaseDB,
        restaurant_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get bookings for a restaurant with optional filters.

        Args:
            db: SupabaseDB instance
            restaurant_id: Restaurant ID
            date_from: Optional start date filter
            date_to: Optional end date filter
            status_filter: Optional status filter
            limit: Maximum records to return
            offset: Number of records to skip

        Returns:
            List of booking dicts
        """
        query = db.table("bookings").select("*").eq("restaurant_id", restaurant_id)

        if date_from:
            query = query.gte("booking_date", str(date_from))
        if date_to:
            query = query.lte("booking_date", str(date_to))
        if status_filter:
            query = query.eq("status", status_filter)

        query = query.order("booking_date", desc=True).order("booking_time", desc=True)
        query = query.range(offset, offset + limit - 1)

        result = query.execute()
        return result.data or []

    def get_bookings_for_customer(
        self,
        db: SupabaseDB,
        customer_id: int,
        include_past: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get bookings for a customer.

        Args:
            db: SupabaseDB instance
            customer_id: Customer ID
            include_past: Whether to include past bookings
            limit: Maximum records to return

        Returns:
            List of booking dicts
        """
        query = db.table("bookings").select("*").eq("customer_id", customer_id)

        if not include_past:
            today = date.today()
            query = query.gte("booking_date", str(today))

        query = query.order("booking_date").order("booking_time")
        query = query.limit(limit)

        result = query.execute()
        return result.data or []

    def get_or_create_customer(
        self,
        db: SupabaseDB,
        phone: str,
        name: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get existing customer by phone or create new one.

        Args:
            db: SupabaseDB instance
            phone: Customer phone number
            name: Customer name (required for new customers)
            email: Customer email (optional)

        Returns:
            Customer dict

        Raises:
            ValueError: If customer not found and name not provided
        """
        customer = db.query_one("customers", {"phone": phone})

        if customer:
            return customer

        if not name:
            raise ValueError("Customer name required for new customers")

        customer_data = {
            "phone": phone,
            "name": name
        }
        if email:
            customer_data["email"] = email

        return db.insert("customers", customer_data)


# Global service instance
booking_service = BookingService()
