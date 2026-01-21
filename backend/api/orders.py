"""
Restaurant Orders API Endpoints

Handles order management for restaurant accounts - listing, viewing details,
and updating order status.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status as http_status
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from collections import defaultdict

from backend.database import get_db, SupabaseDB
from backend.auth import get_current_user

import json
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])

# Valid status values (replacing enum access)
ORDER_STATUSES = ["pending", "confirmed", "preparing", "ready", "out_for_delivery", "picked_up", "delivered", "completed", "cancelled"]
ORDER_TYPES = ["takeout", "delivery"]
PAYMENT_STATUSES = ["unpaid", "paid", "refunded"]


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
        if isinstance(order_items_str, list):
            return order_items_str
        return json.loads(order_items_str) if order_items_str else []
    except json.JSONDecodeError:
        return []


def order_to_response(order: dict) -> OrderResponse:
    """Convert order dict to response."""
    return OrderResponse(
        id=order["id"],
        order_type=order.get("order_type", "takeout"),
        status=order.get("status", "pending"),
        payment_status=order.get("payment_status", "unpaid"),
        payment_method=order.get("payment_method"),
        customer_name=order.get("customer_name"),
        customer_phone=order.get("customer_phone"),
        customer_email=order.get("customer_email"),
        scheduled_time=order.get("scheduled_time"),
        delivery_address=order.get("delivery_address"),
        order_items=parse_order_items(order.get("order_items", "[]")),
        subtotal=order.get("subtotal", 0),
        tax=order.get("tax", 0),
        delivery_fee=order.get("delivery_fee", 0),
        total=order.get("total", 0),
        special_instructions=order.get("special_instructions"),
        conversation_id=order.get("conversation_id"),
        created_at=order.get("created_at"),
        updated_at=order.get("updated_at")
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
    db: SupabaseDB = Depends(get_db)
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
    query = db.table("orders").select("*", count="exact").eq("account_id", account_id)

    # Apply filters
    if order_type:
        query = query.eq("order_type", order_type)

    if status:
        query = query.eq("status", status)

    if payment_status:
        query = query.eq("payment_status", payment_status)

    if date_from:
        query = query.gte("order_date", datetime.combine(date_from, datetime.min.time()).isoformat())

    if date_to:
        query = query.lte("order_date", datetime.combine(date_to, datetime.max.time()).isoformat())

    if search:
        # Supabase uses ilike for case-insensitive search
        query = query.or_(f"customer_name.ilike.%{search}%,customer_phone.ilike.%{search}%")

    # Get total count
    count_result = query.execute()
    total = count_result.count or 0

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    result = db.table("orders").select("*").eq("account_id", account_id)

    # Re-apply filters for the paginated query
    if order_type:
        result = result.eq("order_type", order_type)
    if status:
        result = result.eq("status", status)
    if payment_status:
        result = result.eq("payment_status", payment_status)
    if date_from:
        result = result.gte("order_date", datetime.combine(date_from, datetime.min.time()).isoformat())
    if date_to:
        result = result.lte("order_date", datetime.combine(date_to, datetime.max.time()).isoformat())
    if search:
        result = result.or_(f"customer_name.ilike.%{search}%,customer_phone.ilike.%{search}%")

    result = result.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()
    orders = result.data or []

    return OrderListResponse(
        orders=[order_to_response(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/today", response_model=List[OrderResponse])
async def get_today_orders(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db)
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
    today_start = datetime.combine(today, datetime.min.time()).isoformat()
    today_end = datetime.combine(today, datetime.max.time()).isoformat()

    result = db.table("orders").select("*")\
        .eq("account_id", account_id)\
        .gte("order_date", today_start)\
        .lte("order_date", today_end)\
        .order("scheduled_time", desc=False, nullsfirst=True)\
        .order("created_at", desc=True)\
        .execute()

    orders = result.data or []
    return [order_to_response(o) for o in orders]


@router.get("/upcoming", response_model=List[OrderResponse])
async def get_upcoming_orders(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db)
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
    now = datetime.now().isoformat()

    # Statuses to exclude
    excluded_statuses = ["cancelled", "completed", "picked_up"]

    result = db.table("orders").select("*")\
        .eq("account_id", account_id)\
        .gte("scheduled_time", now)\
        .not_.in_("status", excluded_statuses)\
        .order("scheduled_time", desc=False)\
        .limit(limit)\
        .execute()

    orders = result.data or []
    return [order_to_response(o) for o in orders]


@router.get("/active", response_model=List[OrderResponse])
async def get_active_orders(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db)
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

    active_statuses = ["pending", "confirmed", "preparing", "ready", "out_for_delivery"]

    result = db.table("orders").select("*")\
        .eq("account_id", account_id)\
        .in_("status", active_statuses)\
        .order("scheduled_time", desc=False, nullsfirst=True)\
        .order("created_at", desc=False)\
        .execute()

    orders = result.data or []
    return [order_to_response(o) for o in orders]


@router.get("/stats")
async def get_order_stats(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db)
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

    # Build query
    query = db.table("orders").select("*").eq("account_id", account_id)

    if date_from:
        query = query.gte("order_date", datetime.combine(date_from, datetime.min.time()).isoformat())
    if date_to:
        query = query.lte("order_date", datetime.combine(date_to, datetime.max.time()).isoformat())

    result = query.execute()
    orders = result.data or []

    # Calculate stats
    total_orders = len(orders)
    total_revenue = sum(o.get("total", 0) for o in orders if o.get("status") != "cancelled")
    takeout_orders = len([o for o in orders if o.get("order_type") == "takeout"])
    delivery_orders = len([o for o in orders if o.get("order_type") == "delivery"])
    paid_orders = len([o for o in orders if o.get("payment_status") == "paid"])
    unpaid_orders = len([o for o in orders if o.get("payment_status") == "unpaid"])

    # Status breakdown
    status_counts = {}
    for status in ORDER_STATUSES:
        status_counts[status] = len([o for o in orders if o.get("status") == status])

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
    db: SupabaseDB = Depends(get_db)
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

    order = db.query_one("orders", {"id": order_id, "account_id": account_id})

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
    db: SupabaseDB = Depends(get_db)
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

    order = db.query_one("orders", {"id": order_id, "account_id": account_id})

    if not order:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Validate status
    new_status = request.status
    if new_status not in ORDER_STATUSES:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {request.status}"
        )

    updated_order = db.update("orders", order_id, {
        "status": new_status,
        "updated_at": datetime.now().isoformat()
    })

    logger.info(f"Order {order_id} status updated to {new_status}")

    return order_to_response(updated_order)


@router.patch("/{order_id}/payment", response_model=OrderResponse)
async def update_payment_status(
    order_id: int,
    request: UpdatePaymentStatusRequest,
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db)
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

    order = db.query_one("orders", {"id": order_id, "account_id": account_id})

    if not order:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Validate payment status
    new_status = request.payment_status
    if new_status not in PAYMENT_STATUSES:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment status: {request.payment_status}"
        )

    update_data = {
        "payment_status": new_status,
        "updated_at": datetime.now().isoformat()
    }
    if request.payment_method:
        update_data["payment_method"] = request.payment_method

    updated_order = db.update("orders", order_id, update_data)

    logger.info(f"Order {order_id} payment status updated to {new_status}")

    return order_to_response(updated_order)


# ============== Analytics Endpoints ==============

class PopularItemResponse(BaseModel):
    item_name: str
    quantity_sold: int
    revenue_cents: int
    order_count: int


class DailyTrendResponse(BaseModel):
    date: str
    order_count: int
    revenue_cents: int
    avg_order_value_cents: int


class AnalyticsSummaryResponse(BaseModel):
    period_start: str
    period_end: str
    total_orders: int
    total_revenue_cents: int
    avg_order_value_cents: int
    takeout_orders: int
    delivery_orders: int
    popular_items: List[PopularItemResponse]
    daily_trends: List[DailyTrendResponse]
    peak_hours: Dict[int, int]  # hour -> order count
    repeat_customer_rate: float


@router.get("/analytics/popular-items", response_model=List[PopularItemResponse])
async def get_popular_items(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Number of items to return"),
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db)
):
    """
    Get the most popular menu items based on quantity sold.
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access analytics"
        )

    account_id = current_user["account_id"]
    start_date = (datetime.now() - timedelta(days=days)).isoformat()

    # Get completed orders in the time range (excluding cancelled)
    result = db.table("orders").select("*")\
        .eq("account_id", account_id)\
        .gte("created_at", start_date)\
        .neq("status", "cancelled")\
        .execute()

    orders = result.data or []

    # Aggregate items
    item_stats = defaultdict(lambda: {"quantity": 0, "revenue": 0, "orders": 0})

    for order in orders:
        items = parse_order_items(order.get("order_items", "[]"))
        order_items_seen = set()  # Track unique items per order for order count

        for item in items:
            name = item.get("name", item.get("item_name", "Unknown"))
            quantity = item.get("quantity", 1)
            price = item.get("price_cents", item.get("price", 0))

            item_stats[name]["quantity"] += quantity
            item_stats[name]["revenue"] += price * quantity

            if name not in order_items_seen:
                item_stats[name]["orders"] += 1
                order_items_seen.add(name)

    # Sort by quantity and return top items
    sorted_items = sorted(
        item_stats.items(),
        key=lambda x: x[1]["quantity"],
        reverse=True
    )[:limit]

    return [
        PopularItemResponse(
            item_name=name,
            quantity_sold=stats["quantity"],
            revenue_cents=stats["revenue"],
            order_count=stats["orders"]
        )
        for name, stats in sorted_items
    ]


@router.get("/analytics/trends", response_model=List[DailyTrendResponse])
async def get_order_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db)
):
    """
    Get daily order trends (order count, revenue, average order value).
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access analytics"
        )

    account_id = current_user["account_id"]
    start_date = datetime.now() - timedelta(days=days)
    start_date_iso = start_date.isoformat()

    # Get orders in the time range (excluding cancelled)
    result = db.table("orders").select("*")\
        .eq("account_id", account_id)\
        .gte("created_at", start_date_iso)\
        .neq("status", "cancelled")\
        .execute()

    orders = result.data or []

    # Group by date
    daily_stats = defaultdict(lambda: {"count": 0, "revenue": 0})

    for order in orders:
        created_at = order.get("created_at", "")
        if created_at:
            # Parse ISO format datetime string
            order_date = created_at[:10]  # Get YYYY-MM-DD part
            daily_stats[order_date]["count"] += 1
            daily_stats[order_date]["revenue"] += order.get("total", 0) or 0

    # Fill in missing dates with zeros
    result_list = []
    current = start_date.date()
    end = datetime.now().date()

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        stats = daily_stats.get(date_str, {"count": 0, "revenue": 0})
        avg = stats["revenue"] // stats["count"] if stats["count"] > 0 else 0

        result_list.append(DailyTrendResponse(
            date=date_str,
            order_count=stats["count"],
            revenue_cents=stats["revenue"],
            avg_order_value_cents=avg
        ))
        current += timedelta(days=1)

    return result_list


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db)
):
    """
    Get comprehensive analytics summary including popular items, trends, and metrics.
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only restaurant accounts can access analytics"
        )

    account_id = current_user["account_id"]
    start_date = datetime.now() - timedelta(days=days)
    end_date = datetime.now()
    start_date_iso = start_date.isoformat()

    # Get orders in the time range (excluding cancelled)
    result = db.table("orders").select("*")\
        .eq("account_id", account_id)\
        .gte("created_at", start_date_iso)\
        .neq("status", "cancelled")\
        .execute()

    orders = result.data or []

    # Basic stats
    total_orders = len(orders)
    total_revenue = sum(o.get("total", 0) or 0 for o in orders)
    avg_order_value = total_revenue // total_orders if total_orders > 0 else 0
    takeout_orders = len([o for o in orders if o.get("order_type") == "takeout"])
    delivery_orders = len([o for o in orders if o.get("order_type") == "delivery"])

    # Popular items
    item_stats = defaultdict(lambda: {"quantity": 0, "revenue": 0, "orders": 0})
    for order in orders:
        items = parse_order_items(order.get("order_items", "[]"))
        order_items_seen = set()

        for item in items:
            name = item.get("name", item.get("item_name", "Unknown"))
            quantity = item.get("quantity", 1)
            price = item.get("price_cents", item.get("price", 0))

            item_stats[name]["quantity"] += quantity
            item_stats[name]["revenue"] += price * quantity

            if name not in order_items_seen:
                item_stats[name]["orders"] += 1
                order_items_seen.add(name)

    sorted_items = sorted(
        item_stats.items(),
        key=lambda x: x[1]["quantity"],
        reverse=True
    )[:10]

    popular_items = [
        PopularItemResponse(
            item_name=name,
            quantity_sold=stats["quantity"],
            revenue_cents=stats["revenue"],
            order_count=stats["orders"]
        )
        for name, stats in sorted_items
    ]

    # Daily trends
    daily_stats = defaultdict(lambda: {"count": 0, "revenue": 0})
    for order in orders:
        created_at = order.get("created_at", "")
        if created_at:
            order_date = created_at[:10]  # Get YYYY-MM-DD part
            daily_stats[order_date]["count"] += 1
            daily_stats[order_date]["revenue"] += order.get("total", 0) or 0

    daily_trends = []
    current = start_date.date()
    end = end_date.date()

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        stats = daily_stats.get(date_str, {"count": 0, "revenue": 0})
        avg = stats["revenue"] // stats["count"] if stats["count"] > 0 else 0

        daily_trends.append(DailyTrendResponse(
            date=date_str,
            order_count=stats["count"],
            revenue_cents=stats["revenue"],
            avg_order_value_cents=avg
        ))
        current += timedelta(days=1)

    # Peak hours
    peak_hours = defaultdict(int)
    for order in orders:
        created_at = order.get("created_at", "")
        if created_at:
            # Parse hour from ISO datetime string
            try:
                hour = int(created_at[11:13])  # Get HH from YYYY-MM-DDTHH:MM:SS
                peak_hours[hour] += 1
            except (ValueError, IndexError):
                pass

    # Repeat customer rate
    customer_phones = [o.get("customer_phone") for o in orders if o.get("customer_phone")]
    unique_customers = len(set(customer_phones))
    repeat_rate = 0.0
    if unique_customers > 0 and len(customer_phones) > unique_customers:
        repeat_rate = round((len(customer_phones) - unique_customers) / len(customer_phones) * 100, 1)

    return AnalyticsSummaryResponse(
        period_start=start_date.strftime("%Y-%m-%d"),
        period_end=end_date.strftime("%Y-%m-%d"),
        total_orders=total_orders,
        total_revenue_cents=total_revenue,
        avg_order_value_cents=avg_order_value,
        takeout_orders=takeout_orders,
        delivery_orders=delivery_orders,
        popular_items=popular_items,
        daily_trends=daily_trends,
        peak_hours=dict(peak_hours),
        repeat_customer_rate=repeat_rate
    )
