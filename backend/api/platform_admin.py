"""
Platform admin dashboard endpoints.

Provides platform-level management capabilities for monitoring
all restaurants, revenue, subscriptions, and analytics.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.database import get_db, SupabaseDB

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic schemas

class PlatformStats(BaseModel):
    """Platform-wide statistics."""
    total_restaurants: int
    active_restaurants: int
    trial_restaurants: int
    total_customers: int
    total_orders: int
    total_bookings: int
    total_revenue_cents: int
    platform_commission_cents: int

    class Config:
        from_attributes = True


class RestaurantAccountSummary(BaseModel):
    """Summary of a restaurant account for admin view."""
    id: int
    business_name: str
    owner_name: Optional[str] = None
    owner_email: str
    subscription_tier: str
    subscription_status: str
    is_active: bool
    trial_ends_at: Optional[datetime]
    total_orders: int = 0
    total_revenue_cents: int = 0
    commission_owed_cents: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class RevenueBreakdown(BaseModel):
    """Revenue breakdown for a time period."""
    period_start: datetime
    period_end: datetime
    total_orders: int
    gross_revenue_cents: int
    platform_commission_cents: int
    restaurant_payout_cents: int
    by_restaurant: List[dict]

    class Config:
        from_attributes = True


class SubscriptionUpdate(BaseModel):
    """Update subscription for a restaurant."""
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None

    class Config:
        from_attributes = True


class CommissionSettings(BaseModel):
    """Update commission settings for a restaurant."""
    platform_commission_rate: float = Field(..., ge=0, le=100, description="Commission rate percentage (0-100)")
    commission_enabled: Optional[bool] = Field(default=True, description="Enable or disable commission collection")

    class Config:
        from_attributes = True


class RestaurantCreate(BaseModel):
    """Create new restaurant account."""
    business_name: str = Field(..., min_length=1, max_length=255)
    owner_name: str = Field(..., min_length=1, max_length=255)
    owner_email: str = Field(..., min_length=1, max_length=255)
    owner_phone: Optional[str] = Field(None, max_length=20)
    subscription_tier: str = Field(default="professional")
    subscription_status: str = Field(default="trial")

    class Config:
        from_attributes = True


# Endpoints

@router.get("/stats", response_model=PlatformStats)
async def get_platform_stats(db: SupabaseDB = Depends(get_db)):
    """
    Get platform-wide statistics.

    Returns overview of all restaurants, orders, revenue, and commissions.
    """
    # Count restaurants
    total_restaurants = db.count("restaurant_accounts")
    active_restaurants = db.count("restaurant_accounts", {"is_active": True})
    trial_restaurants = db.count("restaurant_accounts", {"subscription_status": "trial"})

    # Count customers
    total_customers = db.count("customers")

    # Count orders and revenue
    orders = db.query_all("orders", limit=10000)
    total_orders = len(orders)
    orders_sum = sum(order.get("total", 0) or 0 for order in orders)

    # Count bookings
    total_bookings = db.count("bookings")

    # Calculate commission (average 10%)
    platform_commission = int(orders_sum * 0.10)

    return PlatformStats(
        total_restaurants=total_restaurants,
        active_restaurants=active_restaurants,
        trial_restaurants=trial_restaurants,
        total_customers=total_customers,
        total_orders=total_orders,
        total_bookings=total_bookings,
        total_revenue_cents=int(orders_sum),
        platform_commission_cents=platform_commission
    )


@router.get("/restaurants", response_model=List[RestaurantAccountSummary])
async def list_all_restaurants(
    status_filter: Optional[str] = Query(None, description="Filter by subscription status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = 0,
    limit: int = 100,
    db: SupabaseDB = Depends(get_db)
):
    """
    List all restaurant accounts on the platform.

    Includes revenue and commission data for each restaurant.
    """
    # Build filters
    filters = {}
    if status_filter:
        filters["subscription_status"] = status_filter
    if is_active is not None:
        filters["is_active"] = is_active

    accounts = db.query_all(
        "restaurant_accounts",
        filters=filters if filters else None,
        offset=skip,
        limit=limit
    )

    # Enrich with revenue data
    results = []
    for account in accounts:
        account_id = account["id"]

        # Get all restaurant locations for this account
        locations = db.query_all("restaurants", {"account_id": account_id})
        restaurant_ids = [loc["id"] for loc in locations]

        # Calculate order stats
        total_orders = 0
        total_revenue = 0
        for restaurant_id in restaurant_ids:
            orders = db.query_all("orders", {"restaurant_id": restaurant_id}, limit=10000)
            total_orders += len(orders)
            total_revenue += sum(order.get("total", 0) or 0 for order in orders)

        commission_rate = account.get("platform_commission_rate", 10.0) or 10.0
        commission = int(total_revenue * (commission_rate / 100))

        summary = RestaurantAccountSummary(
            id=account["id"],
            business_name=account["business_name"],
            owner_name=account.get("owner_name"),
            owner_email=account["owner_email"],
            subscription_tier=account["subscription_tier"],
            subscription_status=account["subscription_status"],
            is_active=account["is_active"],
            trial_ends_at=account.get("trial_ends_at"),
            total_orders=total_orders,
            total_revenue_cents=total_revenue,
            commission_owed_cents=commission,
            created_at=account["created_at"]
        )
        results.append(summary)

    return results


@router.post("/restaurants", response_model=RestaurantAccountSummary, status_code=201)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    db: SupabaseDB = Depends(get_db)
):
    """
    Create a new restaurant account.

    Creates a restaurant account with basic information. The owner can later
    complete onboarding, add menus, and configure their settings.
    """
    # Check if email already exists
    existing = db.query_one("restaurant_accounts", {"owner_email": restaurant_data.owner_email})

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Restaurant with email {restaurant_data.owner_email} already exists"
        )

    # Create restaurant account
    account_data = {
        "business_name": restaurant_data.business_name,
        "owner_name": restaurant_data.owner_name,
        "owner_email": restaurant_data.owner_email,
        "owner_phone": restaurant_data.owner_phone,
        "subscription_tier": restaurant_data.subscription_tier,
        "subscription_status": restaurant_data.subscription_status,
        "is_active": True,
        "onboarding_completed": False,
        "platform_commission_rate": 10.0,
        "commission_enabled": True
    }

    account = db.insert("restaurant_accounts", account_data)

    return RestaurantAccountSummary(
        id=account["id"],
        business_name=account["business_name"],
        owner_name=account.get("owner_name"),
        owner_email=account["owner_email"],
        subscription_tier=account["subscription_tier"],
        subscription_status=account["subscription_status"],
        is_active=account["is_active"],
        trial_ends_at=account.get("trial_ends_at"),
        total_orders=0,
        total_revenue_cents=0,
        commission_owed_cents=0,
        created_at=account["created_at"]
    )


@router.get("/restaurants/{account_id}/details")
async def get_restaurant_details(account_id: int, db: SupabaseDB = Depends(get_db)):
    """
    Get detailed information about a specific restaurant account.

    Includes locations, menus, orders, bookings, and revenue breakdown.
    """
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    # Get locations
    location_records = db.query_all("restaurants", {"account_id": account_id})
    locations = []
    for location in location_records:
        locations.append({
            "id": location["id"],
            "name": location["name"],
            "address": location.get("address"),
            "phone": location.get("phone")
        })

    # Get menus and items count
    menus = db.query_all("menus", {"account_id": account_id})
    menu_count = len(menus)
    total_menu_items = 0
    for menu in menus:
        categories = db.query_all("menu_categories", {"menu_id": menu["id"]})
        for category in categories:
            items = db.query_all("menu_items", {"category_id": category["id"]})
            total_menu_items += len(items)

    # Get restaurant IDs for queries
    restaurant_ids = [loc["id"] for loc in location_records]

    # Order stats
    total_orders = 0
    total_revenue = 0
    all_orders = []
    for restaurant_id in restaurant_ids:
        orders = db.query_all("orders", {"restaurant_id": restaurant_id}, limit=10000)
        total_orders += len(orders)
        total_revenue += sum(order.get("total", 0) or 0 for order in orders)
        all_orders.extend(orders)

    commission_rate = account.get("platform_commission_rate", 10.0) or 10.0
    commission = int(total_revenue * (commission_rate / 100))

    # Booking stats
    total_bookings = 0
    for restaurant_id in restaurant_ids:
        bookings = db.query_all("bookings", {"restaurant_id": restaurant_id}, limit=10000)
        total_bookings += len(bookings)

    # Recent orders - sort by created_at descending and take top 10
    all_orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    recent_orders = all_orders[:10]

    recent_orders_list = []
    for order in recent_orders:
        recent_orders_list.append({
            "id": order["id"],
            "order_date": order.get("order_date"),
            "total_cents": order.get("total", 0),
            "status": order.get("status"),
            "customer_id": order.get("customer_id")
        })

    return {
        "account": {
            "id": account["id"],
            "business_name": account["business_name"],
            "owner_name": account.get("owner_name"),
            "owner_email": account["owner_email"],
            "owner_phone": account.get("owner_phone"),
            "subscription_tier": account["subscription_tier"],
            "subscription_status": account["subscription_status"],
            "platform_commission_rate": float(account.get("platform_commission_rate", 10.0) or 10.0),
            "is_active": account["is_active"],
            "trial_ends_at": account.get("trial_ends_at"),
            "created_at": account["created_at"]
        },
        "locations": locations,
        "menu_stats": {
            "total_menus": menu_count,
            "total_items": total_menu_items
        },
        "order_stats": {
            "total_orders": total_orders,
            "total_revenue_cents": total_revenue,
            "commission_owed_cents": commission
        },
        "booking_stats": {
            "total_bookings": total_bookings
        },
        "recent_orders": recent_orders_list
    }


@router.get("/revenue", response_model=RevenueBreakdown)
async def get_revenue_breakdown(
    start_date: Optional[datetime] = Query(None, description="Start date for revenue period"),
    end_date: Optional[datetime] = Query(None, description="End date for revenue period"),
    db: SupabaseDB = Depends(get_db)
):
    """
    Get platform revenue breakdown for a time period.

    Includes gross revenue, commission, and per-restaurant breakdown.
    """
    # Default to last 30 days
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()

    # Get all orders in period using Supabase filtering
    query = db.table("orders").select("*").gte("order_date", start_date.isoformat()).lte("order_date", end_date.isoformat())
    result = query.execute()
    orders = result.data or []

    total_orders = len(orders)
    gross_revenue = sum(order.get("total", 0) or 0 for order in orders)

    # Calculate per-restaurant breakdown
    restaurant_revenue = {}
    for order in orders:
        restaurant_id = order.get("restaurant_id")
        if not restaurant_id:
            continue

        restaurant = db.query_one("restaurants", {"id": restaurant_id})
        if restaurant and restaurant.get("account_id"):
            account = db.query_one("restaurant_accounts", {"id": restaurant["account_id"]})
            if account:
                account_id = account["id"]
                if account_id not in restaurant_revenue:
                    commission_rate = account.get("platform_commission_rate", 10.0) or 10.0
                    restaurant_revenue[account_id] = {
                        "account_id": account_id,
                        "business_name": account["business_name"],
                        "orders": 0,
                        "revenue_cents": 0,
                        "commission_rate": float(commission_rate),
                        "commission_cents": 0
                    }

                order_total = order.get("total", 0) or 0
                restaurant_revenue[account_id]["orders"] += 1
                restaurant_revenue[account_id]["revenue_cents"] += order_total
                restaurant_revenue[account_id]["commission_cents"] += int(
                    order_total * (restaurant_revenue[account_id]["commission_rate"] / 100)
                )

    # Calculate total commission
    total_commission = sum(r["commission_cents"] for r in restaurant_revenue.values())
    restaurant_payout = gross_revenue - total_commission

    return RevenueBreakdown(
        period_start=start_date,
        period_end=end_date,
        total_orders=total_orders,
        gross_revenue_cents=gross_revenue,
        platform_commission_cents=total_commission,
        restaurant_payout_cents=restaurant_payout,
        by_restaurant=list(restaurant_revenue.values())
    )


@router.put("/restaurants/{account_id}/subscription", response_model=RestaurantAccountSummary)
async def update_subscription(
    account_id: int,
    subscription_data: SubscriptionUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """
    Update a restaurant's subscription tier or status.

    Used for upgrading/downgrading plans or suspending accounts.
    """
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    update_dict = subscription_data.model_dump(exclude_unset=True)
    if update_dict:
        account = db.update("restaurant_accounts", account_id, update_dict)

    # Get stats for response
    locations = db.query_all("restaurants", {"account_id": account_id})
    restaurant_ids = [loc["id"] for loc in locations]

    total_orders = 0
    total_revenue = 0
    for restaurant_id in restaurant_ids:
        orders = db.query_all("orders", {"restaurant_id": restaurant_id}, limit=10000)
        total_orders += len(orders)
        total_revenue += sum(order.get("total", 0) or 0 for order in orders)

    commission_rate = account.get("platform_commission_rate", 10.0) or 10.0
    commission = int(total_revenue * (commission_rate / 100))

    return RestaurantAccountSummary(
        id=account["id"],
        business_name=account["business_name"],
        owner_name=account.get("owner_name"),
        owner_email=account["owner_email"],
        subscription_tier=account["subscription_tier"],
        subscription_status=account["subscription_status"],
        is_active=account["is_active"],
        trial_ends_at=account.get("trial_ends_at"),
        total_orders=total_orders,
        total_revenue_cents=total_revenue,
        commission_owed_cents=commission,
        created_at=account["created_at"]
    )


@router.put("/restaurants/{account_id}/commission", response_model=RestaurantAccountSummary)
async def update_commission_settings(
    account_id: int,
    commission_data: CommissionSettings,
    db: SupabaseDB = Depends(get_db)
):
    """
    Update a restaurant's commission settings.

    Allows platform admin to:
    - Change commission rate (0-100%)
    - Enable/disable commission collection entirely

    Args:
        account_id: Restaurant account ID
        commission_data: New commission settings

    Returns:
        Updated restaurant account summary with commission details
    """
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    # Update commission settings
    update_data = {
        "platform_commission_rate": commission_data.platform_commission_rate
    }
    if commission_data.commission_enabled is not None:
        update_data["commission_enabled"] = commission_data.commission_enabled

    account = db.update("restaurant_accounts", account_id, update_data)

    # Get stats for response
    locations = db.query_all("restaurants", {"account_id": account_id})
    restaurant_ids = [loc["id"] for loc in locations]

    total_orders = 0
    total_revenue = 0
    for restaurant_id in restaurant_ids:
        orders = db.query_all("orders", {"restaurant_id": restaurant_id}, limit=10000)
        total_orders += len(orders)
        total_revenue += sum(order.get("total", 0) or 0 for order in orders)

    # Calculate commission only if enabled
    commission = 0
    if account.get("commission_enabled", True):
        commission_rate = account.get("platform_commission_rate", 10.0) or 10.0
        commission = int(total_revenue * (commission_rate / 100))

    logger.info(
        f"Updated commission settings for restaurant {account_id}: "
        f"rate={account.get('platform_commission_rate')}%, enabled={account.get('commission_enabled')}"
    )

    return RestaurantAccountSummary(
        id=account["id"],
        business_name=account["business_name"],
        owner_name=account.get("owner_name"),
        owner_email=account["owner_email"],
        subscription_tier=account["subscription_tier"],
        subscription_status=account["subscription_status"],
        is_active=account["is_active"],
        trial_ends_at=account.get("trial_ends_at"),
        total_orders=total_orders,
        total_revenue_cents=total_revenue,
        commission_owed_cents=commission,
        created_at=account["created_at"]
    )


@router.post("/restaurants/{account_id}/suspend")
async def suspend_restaurant(account_id: int, db: SupabaseDB = Depends(get_db)):
    """
    Suspend a restaurant account.

    Prevents them from receiving new orders/bookings.
    """
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    account = db.update("restaurant_accounts", account_id, {
        "is_active": False,
        "subscription_status": "suspended"
    })

    logger.warning(f"Restaurant account suspended: {account['id']} - {account['business_name']}")

    return {
        "status": "success",
        "message": f"Restaurant '{account['business_name']}' has been suspended"
    }


@router.post("/restaurants/{account_id}/activate")
async def activate_restaurant(account_id: int, db: SupabaseDB = Depends(get_db)):
    """
    Reactivate a suspended restaurant account.
    """
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    update_data = {"is_active": True}
    if account.get("subscription_status") == "suspended":
        update_data["subscription_status"] = "active"

    account = db.update("restaurant_accounts", account_id, update_data)

    logger.info(f"Restaurant account activated: {account['id']} - {account['business_name']}")

    return {
        "status": "success",
        "message": f"Restaurant '{account['business_name']}' has been activated"
    }


@router.get("/analytics/growth")
async def get_growth_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: SupabaseDB = Depends(get_db)
):
    """
    Get platform growth analytics.

    Shows trends in restaurant signups, orders, and revenue.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Restaurant signups over time
    accounts_query = db.table("restaurant_accounts").select("*").gte("created_at", start_date.isoformat())
    accounts_result = accounts_query.execute()
    accounts = accounts_result.data or []

    # Group signups by date
    signups_by_date = {}
    for account in accounts:
        created_at = account.get("created_at", "")
        if created_at:
            date_str = created_at[:10]  # Get YYYY-MM-DD
            signups_by_date[date_str] = signups_by_date.get(date_str, 0) + 1

    # Orders over time
    orders_query = db.table("orders").select("*").gte("order_date", start_date.isoformat())
    orders_result = orders_query.execute()
    orders = orders_result.data or []

    # Group orders by date
    orders_by_date = {}
    for order in orders:
        order_date = order.get("order_date", "")
        if order_date:
            date_str = order_date[:10]  # Get YYYY-MM-DD
            if date_str not in orders_by_date:
                orders_by_date[date_str] = {"orders": 0, "revenue": 0}
            orders_by_date[date_str]["orders"] += 1
            orders_by_date[date_str]["revenue"] += order.get("total", 0) or 0

    # Bookings over time
    bookings_query = db.table("bookings").select("*").gte("booking_date", start_date.isoformat())
    bookings_result = bookings_query.execute()
    bookings = bookings_result.data or []

    # Group bookings by date
    bookings_by_date = {}
    for booking in bookings:
        booking_date = booking.get("booking_date", "")
        if booking_date:
            date_str = booking_date[:10]  # Get YYYY-MM-DD
            bookings_by_date[date_str] = bookings_by_date.get(date_str, 0) + 1

    return {
        "period": {
            "start": start_date,
            "end": end_date,
            "days": days
        },
        "restaurant_signups": [
            {"date": date, "count": count}
            for date, count in sorted(signups_by_date.items())
        ],
        "daily_orders": [
            {"date": date, "orders": data["orders"], "revenue_cents": int(data["revenue"])}
            for date, data in sorted(orders_by_date.items())
        ],
        "daily_bookings": [
            {"date": date, "bookings": count}
            for date, count in sorted(bookings_by_date.items())
        ]
    }


# ============== Notifications ==============

class NotificationResponse(BaseModel):
    """Admin notification response."""
    id: int
    notification_type: str
    title: str
    message: str
    account_id: Optional[int]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, description="Max notifications to return"),
    db: SupabaseDB = Depends(get_db)
):
    """
    Get admin notifications.

    Includes new restaurant signups, trial expirations, etc.
    """
    filters = {}
    if unread_only:
        filters["is_read"] = False

    notifications = db.query_all(
        "admin_notifications",
        filters=filters if filters else None,
        order_by="created_at",
        order_desc=True,
        limit=limit
    )

    return notifications


@router.get("/notifications/count")
async def get_notification_count(db: SupabaseDB = Depends(get_db)):
    """Get count of unread notifications."""
    count = db.count("admin_notifications", {"is_read": False})

    return {"unread_count": count}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: SupabaseDB = Depends(get_db)
):
    """Mark a notification as read."""
    notification = db.query_one("admin_notifications", {"id": notification_id})

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    db.update("admin_notifications", notification_id, {"is_read": True})

    return {"status": "success"}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(db: SupabaseDB = Depends(get_db)):
    """Mark all notifications as read."""
    # Get all unread notifications
    unread = db.query_all("admin_notifications", {"is_read": False}, limit=10000)

    # Update each one
    for notification in unread:
        db.update("admin_notifications", notification["id"], {"is_read": True})

    return {"status": "success"}
