"""
SQLAlchemy ORM models for Restaurant Reservation System.

This module defines the database models for restaurants, tables, customers,
and bookings with proper relationships and constraints.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Time,
    UniqueConstraint, CheckConstraint, Index, Text
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from backend.database import Base


class BookingStatus(str, Enum):
    """Enum for booking status values."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class TableLocation(str, Enum):
    """Enum for table location values."""
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    WINDOW = "window"
    PRIVATE = "private"
    BAR = "bar"


class OrderStatus(str, Enum):
    """Enum for order status values."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryStatus(str, Enum):
    """Enum for delivery status values."""
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"


class Restaurant(Base):
    """
    Restaurant model representing a dining establishment.
    
    Attributes:
        id: Primary key
        name: Restaurant name
        address: Full address
        phone: Contact phone number
        email: Contact email
        opening_time: Daily opening time
        closing_time: Daily closing time
        booking_duration_minutes: Default booking duration
        max_party_size: Maximum party size allowed
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("restaurant_accounts.id", ondelete="CASCADE"), nullable=True)  # Nullable for migration
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    opening_time = Column(Time, nullable=False)
    closing_time = Column(Time, nullable=False)
    booking_duration_minutes = Column(Integer, nullable=False, default=90)
    max_party_size = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    account = relationship("RestaurantAccount", back_populates="locations")
    tables = relationship("Table", back_populates="restaurant", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="restaurant", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('booking_duration_minutes > 0', name='check_booking_duration_positive'),
        CheckConstraint('max_party_size > 0', name='check_max_party_size_positive'),
        CheckConstraint('opening_time < closing_time', name='check_opening_before_closing'),
    )
    
    @validates('email')
    def validate_email(self, key: str, email: str) -> str:
        """Validate email format."""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")
        return email.lower().strip()
    
    @validates('phone')
    def validate_phone(self, key: str, phone: str) -> str:
        """Validate and normalize phone number."""
        # Remove common formatting characters
        cleaned = ''.join(filter(str.isdigit, phone))
        if len(cleaned) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return cleaned
    
    def __repr__(self) -> str:
        return f"<Restaurant(id={self.id}, name='{self.name}')>"


class Table(Base):
    """
    Table model representing a dining table in a restaurant.
    
    Attributes:
        id: Primary key
        restaurant_id: Foreign key to restaurant
        table_number: Table identifier within restaurant
        capacity: Maximum number of seats
        location: Table location (indoor, outdoor, etc.)
        is_active: Whether table is available for bookings
        created_at: Record creation timestamp
    """
    __tablename__ = "tables"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    table_number = Column(String(20), nullable=False)
    capacity = Column(Integer, nullable=False)
    location = Column(String(50), nullable=True)  # Optional location description
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="tables")
    bookings = relationship("Booking", back_populates="table")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('restaurant_id', 'table_number', name='uq_restaurant_table_number'),
        CheckConstraint('capacity > 0', name='check_capacity_positive'),
        Index('idx_restaurant_active_tables', 'restaurant_id', 'is_active'),
    )
    
    @validates('location')
    def validate_location(self, key: str, location: str) -> str:
        """Validate table location."""
        if location not in [loc.value for loc in TableLocation]:
            raise ValueError(f"Invalid table location: {location}")
        return location
    
    def __repr__(self) -> str:
        return f"<Table(id={self.id}, number='{self.table_number}', capacity={self.capacity})>"


class Customer(Base):
    """
    Customer model representing a person making reservations.
    
    Attributes:
        id: Primary key
        phone: Primary contact phone number (unique identifier)
        name: Customer full name
        email: Optional email address
        notes: Internal notes about customer
        total_bookings: Total number of bookings made
        no_shows: Number of no-show incidents
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    total_bookings = Column(Integer, nullable=False, default=0)
    no_shows = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    bookings = relationship("Booking", back_populates="customer")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('total_bookings >= 0', name='check_total_bookings_non_negative'),
        CheckConstraint('no_shows >= 0', name='check_no_shows_non_negative'),
        CheckConstraint('no_shows <= total_bookings', name='check_no_shows_lte_total'),
    )
    
    @validates('email')
    def validate_email(self, key: str, email: Optional[str]) -> Optional[str]:
        """Validate email format if provided."""
        if email:
            if '@' not in email:
                raise ValueError("Invalid email format")
            return email.lower().strip()
        return email
    
    @validates('phone')
    def validate_phone(self, key: str, phone: str) -> str:
        """Validate and normalize phone number."""
        # Remove common formatting characters
        cleaned = ''.join(filter(str.isdigit, phone))
        if len(cleaned) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return cleaned
    
    @property
    def no_show_rate(self) -> float:
        """Calculate customer's no-show rate."""
        if self.total_bookings == 0:
            return 0.0
        return (self.no_shows / self.total_bookings) * 100
    
    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name='{self.name}', phone='{self.phone}')>"


class Booking(Base):
    """
    Booking model representing a table reservation.
    
    Attributes:
        id: Primary key
        restaurant_id: Foreign key to restaurant
        table_id: Foreign key to assigned table
        customer_id: Foreign key to customer
        booking_date: Date of reservation
        booking_time: Time of reservation
        party_size: Number of guests
        duration_minutes: Expected duration of dining
        status: Current booking status
        special_requests: Any special requests or notes
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    table_id = Column(Integer, ForeignKey("tables.id", ondelete="RESTRICT"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    booking_date = Column(DateTime(timezone=True), nullable=False)
    booking_time = Column(Time, nullable=False)
    party_size = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default=BookingStatus.PENDING)
    special_requests = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="bookings")
    table = relationship("Table", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('party_size > 0', name='check_party_size_positive'),
        CheckConstraint('duration_minutes > 0', name='check_duration_positive'),
        Index('idx_restaurant_date_status', 'restaurant_id', 'booking_date', 'status'),
        Index('idx_customer_bookings', 'customer_id', 'booking_date'),
        Index('idx_table_date_time', 'table_id', 'booking_date', 'booking_time'),
    )
    
    @validates('status')
    def validate_status(self, key: str, status: str) -> str:
        """Validate booking status."""
        if status not in [s.value for s in BookingStatus]:
            raise ValueError(f"Invalid booking status: {status}")
        return status
    
    @validates('booking_date')
    def validate_booking_date(self, key: str, booking_date) -> datetime:
        """Validate booking date is not in the past."""
        from datetime import date as date_type
        # Handle both date and datetime objects
        check_date = booking_date if isinstance(booking_date, date_type) else booking_date.date()
        if check_date < datetime.now().date():
            raise ValueError("Booking date cannot be in the past")
        return booking_date
    
    @property
    def booking_datetime(self) -> datetime:
        """Combine booking date and time into a single datetime."""
        return datetime.combine(self.booking_date.date(), self.booking_time)
    
    @property
    def end_time(self) -> Time:
        """Calculate booking end time."""
        from datetime import timedelta
        end_datetime = self.booking_datetime + timedelta(minutes=self.duration_minutes)
        return end_datetime.time()
    
    def overlaps_with(self, other: 'Booking') -> bool:
        """Check if this booking overlaps with another booking."""
        if self.table_id != other.table_id or self.booking_date.date() != other.booking_date.date():
            return False
        
        # Calculate start and end times for both bookings
        self_start = self.booking_datetime
        self_end = self_start + timedelta(minutes=self.duration_minutes)
        other_start = other.booking_datetime
        other_end = other_start + timedelta(minutes=other.duration_minutes)
        
        # Check for overlap
        return not (self_end <= other_start or self_start >= other_end)
    
    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, date={self.booking_date}, time={self.booking_time}, status={self.status})>"

class Order(Base):
    """
    Order model representing a food order for delivery or pickup.
    
    Attributes:
        id: Primary key
        restaurant_id: Foreign key to restaurant
        customer_id: Foreign key to customer
        order_date: Date and time order was placed
        delivery_address: Delivery address
        order_items: JSON field with order items
        subtotal: Order subtotal in cents
        tax: Tax amount in cents
        delivery_fee: Delivery fee in cents
        total: Total amount in cents
        status: Current order status
        special_instructions: Special delivery or preparation instructions
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    delivery_address = Column(Text, nullable=False)
    order_items = Column(Text, nullable=False)  # JSON string of items
    subtotal = Column(Integer, nullable=False)  # in cents
    tax = Column(Integer, nullable=False, default=0)
    delivery_fee = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default=OrderStatus.PENDING)
    special_instructions = Column(Text, nullable=True)

    # Payment fields
    payment_status = Column(String(20), nullable=False, default='unpaid')  # paid, unpaid, pending
    payment_method = Column(String(30), nullable=True)  # card, cash, pay_on_arrival
    payment_intent_id = Column(String(255), nullable=True)  # Stripe payment intent ID

    # Customer info (denormalized for quick access)
    customer_name = Column(String(100), nullable=True)
    customer_phone = Column(String(20), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    restaurant = relationship("Restaurant", backref="orders")
    customer = relationship("Customer", backref="orders")
    delivery = relationship("Delivery", back_populates="order", uselist=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('subtotal >= 0', name='check_subtotal_non_negative'),
        CheckConstraint('tax >= 0', name='check_tax_non_negative'),
        CheckConstraint('delivery_fee >= 0', name='check_delivery_fee_non_negative'),
        CheckConstraint('total >= 0', name='check_total_non_negative'),
        Index('idx_order_status', 'status'),
        Index('idx_customer_orders', 'customer_id', 'order_date'),
    )
    
    @validates('status')
    def validate_status(self, key: str, status: str) -> str:
        """Validate order status."""
        if status not in [s.value for s in OrderStatus]:
            raise ValueError(f"Invalid order status: {status}")
        return status
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, status={self.status}, total=${self.total/100:.2f})>"


class Delivery(Base):
    """
    Delivery model representing a delivery for an order.
    
    Attributes:
        id: Primary key
        order_id: Foreign key to order
        driver_name: Name of delivery driver
        driver_phone: Driver's phone number
        estimated_delivery_time: Estimated delivery time
        actual_delivery_time: Actual delivery time
        status: Current delivery status
        tracking_notes: Internal tracking notes
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    driver_name = Column(String(255), nullable=True)
    driver_phone = Column(String(20), nullable=True)
    estimated_delivery_time = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default=DeliveryStatus.ASSIGNED)
    tracking_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="delivery")
    
    # Constraints
    __table_args__ = (
        Index('idx_delivery_status', 'status'),
    )
    
    @validates('status')
    def validate_status(self, key: str, status: str) -> str:
        """Validate delivery status."""
        if status not in [s.value for s in DeliveryStatus]:
            raise ValueError(f"Invalid delivery status: {status}")
        return status
    
    @validates('driver_phone')
    def validate_phone(self, key: str, phone: Optional[str]) -> Optional[str]:
        """Validate and normalize driver phone number."""
        if phone:
            cleaned = ''.join(filter(str.isdigit, phone))
            if len(cleaned) < 10:
                raise ValueError("Phone number must have at least 10 digits")
            return cleaned
        return phone
    
    def __repr__(self) -> str:
        return f"<Delivery(id={self.id}, order_id={self.order_id}, status={self.status})>"
