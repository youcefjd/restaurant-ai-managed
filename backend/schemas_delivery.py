"""
Pydantic schemas for delivery and order management.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from backend.models import OrderStatus, DeliveryStatus


# Order Schemas

class OrderItemSchema(BaseModel):
    """Individual order item."""
    name: str = Field(..., description="Item name")
    quantity: int = Field(..., ge=1, description="Quantity")
    price_cents: int = Field(..., ge=0, description="Price per item in cents")
    notes: Optional[str] = Field(None, description="Special instructions for this item")


class OrderCreate(BaseModel):
    """Schema for creating a new order."""
    restaurant_id: int = Field(..., description="Restaurant ID")
    customer_phone: str = Field(..., description="Customer phone number")
    customer_name: Optional[str] = Field(None, description="Customer name (required for new customers)")
    customer_email: Optional[str] = Field(None, description="Customer email")
    delivery_address: str = Field(..., description="Delivery address")
    order_items: str = Field(..., description="Order items as JSON string")
    subtotal: int = Field(..., ge=0, description="Subtotal in cents")
    tax: int = Field(0, ge=0, description="Tax amount in cents")
    delivery_fee: int = Field(0, ge=0, description="Delivery fee in cents")
    total: int = Field(..., ge=0, description="Total amount in cents")
    special_instructions: Optional[str] = Field(None, description="Special delivery or preparation instructions")

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    status: Optional[str] = Field(None, description="Order status")
    special_instructions: Optional[str] = Field(None, description="Special instructions")

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Schema for order response."""
    id: int
    restaurant_id: int
    customer_id: int
    order_date: datetime
    delivery_address: str
    order_items: str
    subtotal: int
    tax: int
    delivery_fee: int
    total: int
    status: str
    special_instructions: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Delivery Schemas

class DeliveryCreate(BaseModel):
    """Schema for creating a delivery."""
    order_id: int = Field(..., description="Order ID")
    driver_name: Optional[str] = Field(None, description="Driver name")
    driver_phone: Optional[str] = Field(None, description="Driver phone number")
    estimated_delivery_time: Optional[datetime] = Field(None, description="Estimated delivery time")

    class Config:
        from_attributes = True


class DeliveryUpdate(BaseModel):
    """Schema for updating a delivery."""
    driver_name: Optional[str] = Field(None, description="Driver name")
    driver_phone: Optional[str] = Field(None, description="Driver phone number")
    status: Optional[str] = Field(None, description="Delivery status")
    actual_delivery_time: Optional[datetime] = Field(None, description="Actual delivery time")
    tracking_notes: Optional[str] = Field(None, description="Tracking notes")

    class Config:
        from_attributes = True


class DeliveryResponse(BaseModel):
    """Schema for delivery response."""
    id: int
    order_id: int
    driver_name: Optional[str]
    driver_phone: Optional[str]
    estimated_delivery_time: Optional[datetime]
    actual_delivery_time: Optional[datetime]
    status: str
    tracking_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderWithDelivery(OrderResponse):
    """Schema for order with delivery details."""
    delivery: Optional[DeliveryResponse] = None

    class Config:
        from_attributes = True
