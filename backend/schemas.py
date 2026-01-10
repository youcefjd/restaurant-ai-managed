"""
Pydantic schemas for Restaurant Reservation System.

Handles request/response validation and serialization for all API endpoints.
"""

from datetime import date, datetime, time
from typing import Optional, List, Literal
from enum import Enum

from pydantic import BaseModel, Field, validator, EmailStr, constr


class BookingStatus(str, Enum):
    """Enum for booking status values."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class TableLocation(str, Enum):
    """Enum for table location values."""
    WINDOW = "window"
    PATIO = "patio"
    MAIN = "main"
    PRIVATE = "private"
    BAR = "bar"


# Base schemas with common fields
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime
    updated_at: Optional[datetime] = None


# Restaurant schemas
class RestaurantBase(BaseModel):
    """Base schema for restaurant data."""
    name: constr(min_length=1, max_length=100) = Field(..., description="Restaurant name")
    address: constr(min_length=1, max_length=200) = Field(..., description="Restaurant address")
    phone: constr(regex=r'^\+?1?\d{9,15}$') = Field(..., description="Phone number")
    email: EmailStr = Field(..., description="Contact email")
    opening_time: time = Field(..., description="Daily opening time")
    closing_time: time = Field(..., description="Daily closing time")
    booking_duration_minutes: int = Field(default=120, ge=30, le=300, description="Default booking duration")
    max_party_size: int = Field(default=10, ge=1, le=50, description="Maximum party size")

    @validator('closing_time')
    def validate_closing_after_opening(cls, v, values):
        """Ensure closing time is after opening time."""
        if 'opening_time' in values and v <= values['opening_time']:
            raise ValueError('Closing time must be after opening time')
        return v


class RestaurantCreate(RestaurantBase):
    """Schema for creating a restaurant."""
    pass


class RestaurantUpdate(BaseModel):
    """Schema for updating a restaurant."""
    name: Optional[constr(min_length=1, max_length=100)] = None
    address: Optional[constr(min_length=1, max_length=200)] = None
    phone: Optional[constr(regex=r'^\+?1?\d{9,15}$')] = None
    email: Optional[EmailStr] = None
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    booking_duration_minutes: Optional[int] = Field(None, ge=30, le=300)
    max_party_size: Optional[int] = Field(None, ge=1, le=50)

    @validator('closing_time')
    def validate_closing_after_opening(cls, v, values):
        """Ensure closing time is after opening time if both provided."""
        if v and 'opening_time' in values and values['opening_time']:
            if v <= values['opening_time']:
                raise ValueError('Closing time must be after opening time')
        return v


class Restaurant(RestaurantBase, TimestampMixin):
    """Schema for restaurant response."""
    id: int

    class Config:
        """Pydantic config."""
        from_attributes = True


# Table schemas
class TableBase(BaseModel):
    """Base schema for table data."""
    restaurant_id: int = Field(..., description="Restaurant ID")
    table_number: constr(min_length=1, max_length=10) = Field(..., description="Table identifier")
    capacity: int = Field(..., ge=1, le=20, description="Maximum seats")
    location: TableLocation = Field(default=TableLocation.MAIN, description="Table location")
    is_active: bool = Field(default=True, description="Whether table is available for booking")


class TableCreate(TableBase):
    """Schema for creating a table."""
    pass


class TableUpdate(BaseModel):
    """Schema for updating a table."""
    table_number: Optional[constr(min_length=1, max_length=10)] = None
    capacity: Optional[int] = Field(None, ge=1, le=20)
    location: Optional[TableLocation] = None
    is_active: Optional[bool] = None


class Table(TableBase):
    """Schema for table response."""
    id: int
    created_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


# Customer schemas
class CustomerBase(BaseModel):
    """Base schema for customer data."""
    phone: constr(regex=r'^\+?1?\d{9,15}$') = Field(..., description="Primary phone number")
    name: constr(min_length=1, max_length=100) = Field(..., description="Customer name")
    email: Optional[EmailStr] = Field(None, description="Customer email")
    notes: Optional[constr(max_length=500)] = Field(None, description="Special notes")


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    name: Optional[constr(min_length=1, max_length=100)] = None
    email: Optional[EmailStr] = None
    notes: Optional[constr(max_length=500)] = None


class Customer(CustomerBase, TimestampMixin):
    """Schema for customer response."""
    id: int
    total_bookings: int = Field(default=0, description="Total bookings made")
    no_shows: int = Field(default=0, description="Number of no-shows")

    class Config:
        """Pydantic config."""
        from_attributes = True


# Booking schemas
class BookingBase(BaseModel):
    """Base schema for booking data."""
    restaurant_id: int = Field(..., description="Restaurant ID")
    booking_date: date = Field(..., description="Reservation date")
    booking_time: time = Field(..., description="Reservation time")
    party_size: int = Field(..., ge=1, description="Number of guests")
    special_requests: Optional[constr(max_length=500)] = Field(None, description="Special requests")

    @validator('booking_date')
    def validate_future_date(cls, v):
        """Ensure booking date is not in the past."""
        if v < date.today():
            raise ValueError('Booking date cannot be in the past')
        return v


class BookingCreate(BookingBase):
    """Schema for creating a booking."""
    customer_phone: constr(regex=r'^\+?1?\d{9,15}$') = Field(..., description="Customer phone number")
    customer_name: Optional[constr(min_length=1, max_length=100)] = Field(None, description="Customer name (for new customers)")
    customer_email: Optional[EmailStr] = Field(None, description="Customer email (for new customers)")
    duration_minutes: Optional[int] = Field(None, ge=30, le=300, description="Custom duration")


class BookingUpdate(BaseModel):
    """Schema for updating a booking."""
    booking_date: Optional[date] = None
    booking_time: Optional[time] = None
    party_size: Optional[int] = Field(None, ge=1)
    duration_minutes: Optional[int] = Field(None, ge=30, le=300)
    special_requests: Optional[constr(max_length=500)] = None
    status: Optional[BookingStatus] = None

    @validator('booking_date')
    def validate_future_date(cls, v):
        """Ensure booking date is not in the past."""
        if v and v < date.today():
            raise ValueError('Booking date cannot be in the past')
        return v


class Booking(BookingBase, TimestampMixin):
    """Schema for booking response."""
    id: int
    table_id: int
    customer_id: int
    duration_minutes: int
    status: BookingStatus
    customer: Optional[Customer] = None
    table: Optional[Table] = None
    restaurant: Optional[Restaurant] = None

    class Config:
        """Pydantic config."""
        from_attributes = True


# Availability schemas
class AvailabilityQuery(BaseModel):
    """Schema for availability check query."""
    restaurant_id: int = Field(..., description="Restaurant ID")
    date: date = Field(..., description="Desired date")
    time: time = Field(..., description="Desired time")
    party_size: int = Field(..., ge=1, description="Number of guests")
    duration_minutes: Optional[int] = Field(None, ge=30, le=300, description="Custom duration")

    @validator('date')
    def validate_future_date(cls, v):
        """Ensure date is not in the past."""
        if v < date.today():
            raise ValueError('Date cannot be in the past')
        return v


class TimeSlot(BaseModel):
    """Schema for available time slot."""
    time: time
    available_tables: List[int] = Field(..., description="List of available table IDs")
    total_capacity: int = Field(..., description="Total available capacity")


class AvailabilityResponse(BaseModel):
    """Schema for availability check response."""
    requested_time: time
    is_available: bool
    available_tables: List[Table] = Field(default_factory=list)
    alternative_times: List[TimeSlot] = Field(default_factory=list, description="Alternative time slots if requested time unavailable")
    message: Optional[str] = None


# List response schemas with pagination
class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of records to return")


class RestaurantList(BaseModel):
    """Schema for paginated restaurant list."""
    items: List[Restaurant]
    total: int
    skip: int
    limit: int


class TableList(BaseModel):
    """Schema for paginated table list."""
    items: List[Table]
    total: int
    skip: int
    limit: int


class BookingList(BaseModel):
    """Schema for paginated booking list."""
    items: List[Booking]
    total: int
    skip: int
    limit: int


# Filter schemas
class BookingFilters(BaseModel):
    """Schema for booking list filters."""
    status: Optional[BookingStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    customer_phone: Optional[str] = None
    table_id: Optional[int] = None

    @validator('date_to')
    def validate_date_range(cls, v, values):
        """Ensure date_to is after date_from."""
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('date_to must be after date_from')
        return v


# Error response schemas
class ErrorDetail(BaseModel):
    """Schema for error details."""
    loc: Optional[List[str]] = None
    msg: str
    type: str


class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str
    errors: Optional[List[ErrorDetail]] = None
    status_code: int


# Success response schemas
class SuccessResponse(BaseModel):
    """Schema for success response."""
    message: str
    data: Optional[dict] = None


# Booking confirmation schema
class BookingConfirmation(BaseModel):
    """Schema for booking confirmation response."""
    booking: Booking
    confirmation_code: str
    message: str