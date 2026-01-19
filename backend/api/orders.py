"""
Restaurant Orders API Endpoints

Handles order management for restaurant accounts - listing, viewing details,
and updating order status.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status as http_status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

from backend.database import get_db
from backend.models import Order, OrderStatus, OrderType, PaymentStatus
from backend.auth import get_current_user

import json
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


# Pydantic models
class OrderItemResponse(BaseModel):
    name: str
    quantity: int
    price_cents: int
    modifiers: Optional[List[str]] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    order_type: str
    status: str
    payment_status: str
    payment_method: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_email: Optional[str]
    scheduled_time: Optional[datetime]
    delivery_address: Optional[str]
    order_items: List[dict]
    subtotal: int
    tax: int
    delivery_fee: int
    total: int
    special_instructions: Optional[str]
    conversation_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int


class UpdateOrderStatusRequest(BaseModel):
    status: str


class UpdatePaymentStatusRequest(BaseModel):
    payment_status: str
    payment_method: Optional[str] = None


def parse_order_items(order_items_str: str) -> List[dict]:
    """Parse order items from JSON string."""
    try:
        return json.loads(order_items_str) if order_items_str else []
    except json.JSONDecodeError:
        return []


def order_to_response(order: Order) -> OrderResponse:
    """Convert Order model to response."""
    return OrderResponse(
        id=order.id,
        order_type=order.order_type,
        status=order.status,
        payment_status=order.payment_status,
        payment_method=order.payment_method,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_email=order.customer_email,
        scheduled_time=order.scheduled_time,
        delivery_address=order.delivery_address,
        order_items=parse_order_items(order.order_items),
        subtotal=order.subtotal,
        tax=order.tax,
        delivery_fee=order.delivery_fee,
        total=order.total,
        special_instructions=order.special_instructions,
        conversation_id=order.conversation_id,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.get("", response_model=OrderListResponse)
async def list_orders(
    order_type: Optional[str] = Query(None, description="Filter by order type (takeout/delivery)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    date_from: Optional[date] = Query(None, description="Filter orders from this date"),
    date_to: Optional[date] = Query(None, description="Filter orders to this date"),
    search: Optional[str] = Query(None, description="Search by customer name or phone"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List orders for the current restaurant account.

    Supports filtering by order type, status, payment status, date range, and search.
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access orders"
        )

    account_id = current_user["account_id"]

    # Build query
    query = db.query(Order).filter(Order.account_id == account_id)

    # Apply filters
    if order_type:
        query = query.filter(Order.order_type == order_type)

    if status:
        query = query.filter(Order.status == status)

    if payment_status:
        query = query.filter(Order.payment_status == payment_status)

    if date_from:
        query = query.filter(Order.order_date >= datetime.combine(date_from, datetime.min.time()))

    if date_to:
        query = query.filter(Order.order_date <= datetime.combine(date_to, datetime.max.time()))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Order.customer_name.ilike(search_term),
                Order.customer_phone.ilike(search_term)
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    orders = query.order_by(desc(Order.created_at))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()

    return OrderListResponse(
        orders=[order_to_response(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/today", response_model=List[OrderResponse])
async def get_today_orders(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all orders for today (for dashboard view).
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access orders"
        )

    account_id = current_user["account_id"]
    today = date.today()

    orders = db.query(Order).filter(
        Order.account_id == account_id,
        Order.order_date >= datetime.combine(today, datetime.min.time()),
        Order.order_date <= datetime.combine(today, datetime.max.time())
    ).order_by(Order.scheduled_time.asc().nullsfirst(), desc(Order.created_at)).all()

    return [order_to_response(o) for o in orders]


@router.get("/upcoming", response_model=List[OrderResponse])
async def get_upcoming_orders(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get upcoming scheduled orders (for dashboard view).

    Returns orders with scheduled_time in the future, ordered by scheduled_time.
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access orders"
        )

    account_id = current_user["account_id"]
    now = datetime.now()

    orders = db.query(Order).filter(
        Order.account_id == account_id,
        Order.scheduled_time >= now,
        Order.status.notin_([OrderStatus.CANCELLED.value, OrderStatus.COMPLETED.value, OrderStatus.PICKED_UP.value])
    ).order_by(Order.scheduled_time.asc()).limit(limit).all()

    return [order_to_response(o) for o in orders]


@router.get("/active", response_model=List[OrderResponse])
async def get_active_orders(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active orders (not completed/cancelled).
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access orders"
        )

    account_id = current_user["account_id"]

    active_statuses = [
        OrderStatus.PENDING.value,
        OrderStatus.CONFIRMED.value,
        OrderStatus.PREPARING.value,
        OrderStatus.READY.value,
        OrderStatus.OUT_FOR_DELIVERY.value
    ]

    orders = db.query(Order).filter(
        Order.account_id == account_id,
        Order.status.in_(active_statuses)
    ).order_by(Order.scheduled_time.asc().nullsfirst(), Order.created_at.asc()).all()

    return [order_to_response(o) for o in orders]


@router.get("/stats")
async def get_order_stats(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get order statistics for the restaurant.
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access orders"
        )

    account_id = current_user["account_id"]

    # Base query
    query = db.query(Order).filter(Order.account_id == account_id)

    if date_from:
        query = query.filter(Order.order_date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Order.order_date <= datetime.combine(date_to, datetime.max.time()))

    orders = query.all()

    # Calculate stats
    total_orders = len(orders)
    total_revenue = sum(o.total for o in orders if o.status not in [OrderStatus.CANCELLED.value])
    takeout_orders = len([o for o in orders if o.order_type == OrderType.TAKEOUT.value])
    delivery_orders = len([o for o in orders if o.order_type == OrderType.DELIVERY.value])
    paid_orders = len([o for o in orders if o.payment_status == PaymentStatus.PAID.value])
    unpaid_orders = len([o for o in orders if o.payment_status == PaymentStatus.UNPAID.value])

    # Status breakdown
    status_counts = {}
    for status in OrderStatus:
        status_counts[status.value] = len([o for o in orders if o.status == status.value])

    return {
        "total_orders": total_orders,
        "total_revenue_cents": total_revenue,
        "takeout_orders": takeout_orders,
        "delivery_orders": delivery_orders,
        "paid_orders": paid_orders,
        "unpaid_orders": unpaid_orders,
        "status_breakdown": status_counts
    }


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific order by ID.
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access orders"
        )

    account_id = current_user["account_id"]

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.account_id == account_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return order_to_response(order)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    request: UpdateOrderStatusRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update order status.

    Valid status transitions:
    - pending -> confirmed, cancelled
    - confirmed -> preparing, cancelled
    - preparing -> ready, cancelled
    - ready -> picked_up (takeout), out_for_delivery (delivery), cancelled
    - out_for_delivery -> delivered, cancelled
    - picked_up/delivered -> completed
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access orders"
        )

    account_id = current_user["account_id"]

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.account_id == account_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Validate status
    try:
        new_status = OrderStatus(request.status)
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {request.status}"
        )

    order.status = new_status.value
    db.commit()
    db.refresh(order)

    logger.info(f"Order {order_id} status updated to {new_status.value}")

    return order_to_response(order)


@router.patch("/{order_id}/payment", response_model=OrderResponse)
async def update_payment_status(
    order_id: int,
    request: UpdatePaymentStatusRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update order payment status.
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access orders"
        )

    account_id = current_user["account_id"]

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.account_id == account_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Validate payment status
    try:
        new_status = PaymentStatus(request.payment_status)
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment status: {request.payment_status}"
        )

    order.payment_status = new_status.value
    if request.payment_method:
        order.payment_method = request.payment_method

    db.commit()
    db.refresh(order)

    logger.info(f"Order {order_id} payment status updated to {new_status.value}")

    return order_to_response(order)
