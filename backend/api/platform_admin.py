"""
Platform admin dashboard endpoints.

Provides platform-level management capabilities for monitoring
all restaurants, revenue, subscriptions, and analytics.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field

from backend.database import get_db
from backend.models_platform import (
    RestaurantAccount, SubscriptionTier, SubscriptionStatus
)
from backend.models import Restaurant, Order, Booking, Customer

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


# Endpoints

@router.get("/stats", response_model=PlatformStats)
async def get_platform_stats(db: Session = Depends(get_db)):
    """
    Get platform-wide statistics.

    Returns overview of all restaurants, orders, revenue, and commissions.
    """
    # Count restaurants
    total_restaurants = db.query(RestaurantAccount).count()
    active_restaurants = db.query(RestaurantAccount).filter(
        RestaurantAccount.is_active == True
    ).count()
    trial_restaurants = db.query(RestaurantAccount).filter(
        RestaurantAccount.subscription_status == SubscriptionStatus.TRIAL.value
    ).count()

    # Count customers
    total_customers = db.query(Customer).count()

    # Count orders and revenue
    total_orders = db.query(Order).count()
    orders_sum = db.query(func.sum(Order.total)).scalar() or 0

    # Count bookings
    total_bookings = db.query(Booking).count()

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
    db: Session = Depends(get_db)
):
    """
    List all restaurant accounts on the platform.

    Includes revenue and commission data for each restaurant.
    """
    query = db.query(RestaurantAccount)

    if status_filter:
        query = query.filter(RestaurantAccount.subscription_status == status_filter)

    if is_active is not None:
        query = query.filter(RestaurantAccount.is_active == is_active)

    accounts = query.offset(skip).limit(limit).all()

    # Enrich with revenue data
    results = []
    for account in accounts:
        # Get all restaurant locations for this account
        restaurant_ids = [r.id for r in account.locations]

        # Calculate order stats
        orders = db.query(Order).filter(Order.restaurant_id.in_(restaurant_ids)).all()
        total_orders = len(orders)
        total_revenue = sum(order.total for order in orders)
        commission = int(total_revenue * (account.platform_commission_rate / 100))

        summary = RestaurantAccountSummary(
            id=account.id,
            business_name=account.business_name,
            owner_name=account.owner_name,
            owner_email=account.owner_email,
            subscription_tier=account.subscription_tier,
            subscription_status=account.subscription_status,
            is_active=account.is_active,
            trial_ends_at=account.trial_ends_at,
            total_orders=total_orders,
            total_revenue_cents=total_revenue,
            commission_owed_cents=commission,
            created_at=account.created_at
        )
        results.append(summary)

    return results


@router.get("/restaurants/{account_id}/details")
async def get_restaurant_details(account_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific restaurant account.

    Includes locations, menus, orders, bookings, and revenue breakdown.
    """
    account = db.query(RestaurantAccount).filter(RestaurantAccount.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    # Get locations
    locations = []
    for location in account.locations:
        locations.append({
            "id": location.id,
            "name": location.name,
            "address": location.address,
            "phone": location.phone
        })

    # Get menu count
    menu_count = len(account.menus)
    total_menu_items = sum(
        len(category.items)
        for menu in account.menus
        for category in menu.categories
    )

    # Get restaurant IDs for queries
    restaurant_ids = [r.id for r in account.locations]

    # Order stats
    orders = db.query(Order).filter(Order.restaurant_id.in_(restaurant_ids)).all()
    total_orders = len(orders)
    total_revenue = sum(order.total for order in orders)
    commission = int(total_revenue * (account.platform_commission_rate / 100))

    # Booking stats
    bookings = db.query(Booking).filter(Booking.restaurant_id.in_(restaurant_ids)).all()
    total_bookings = len(bookings)

    # Recent orders
    recent_orders = db.query(Order).filter(
        Order.restaurant_id.in_(restaurant_ids)
    ).order_by(Order.created_at.desc()).limit(10).all()

    recent_orders_list = []
    for order in recent_orders:
        recent_orders_list.append({
            "id": order.id,
            "order_date": order.order_date,
            "total_cents": order.total,
            "status": order.status,
            "customer_id": order.customer_id
        })

    return {
        "account": {
            "id": account.id,
            "business_name": account.business_name,
            "owner_name": account.owner_name,
            "owner_email": account.owner_email,
            "owner_phone": account.owner_phone,
            "subscription_tier": account.subscription_tier,
            "subscription_status": account.subscription_status,
            "platform_commission_rate": float(account.platform_commission_rate),
            "is_active": account.is_active,
            "trial_ends_at": account.trial_ends_at,
            "created_at": account.created_at
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
    db: Session = Depends(get_db)
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

    # Get all orders in period
    orders = db.query(Order).filter(
        Order.order_date >= start_date,
        Order.order_date <= end_date
    ).all()

    total_orders = len(orders)
    gross_revenue = sum(order.total for order in orders)

    # Calculate per-restaurant breakdown
    restaurant_revenue = {}
    for order in orders:
        restaurant = db.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()
        if restaurant and restaurant.account_id:
            account = db.query(RestaurantAccount).filter(
                RestaurantAccount.id == restaurant.account_id
            ).first()
            if account:
                if account.id not in restaurant_revenue:
                    restaurant_revenue[account.id] = {
                        "account_id": account.id,
                        "business_name": account.business_name,
                        "orders": 0,
                        "revenue_cents": 0,
                        "commission_rate": float(account.platform_commission_rate),
                        "commission_cents": 0
                    }

                restaurant_revenue[account.id]["orders"] += 1
                restaurant_revenue[account.id]["revenue_cents"] += order.total
                restaurant_revenue[account.id]["commission_cents"] += int(
                    order.total * (account.platform_commission_rate / 100)
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
    db: Session = Depends(get_db)
):
    """
    Update a restaurant's subscription tier or status.

    Used for upgrading/downgrading plans or suspending accounts.
    """
    account = db.query(RestaurantAccount).filter(RestaurantAccount.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    update_dict = subscription_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)

    # Get stats for response
    restaurant_ids = [r.id for r in account.locations]
    orders = db.query(Order).filter(Order.restaurant_id.in_(restaurant_ids)).all()
    total_orders = len(orders)
    total_revenue = sum(order.total for order in orders)
    commission = int(total_revenue * (account.platform_commission_rate / 100))

    return RestaurantAccountSummary(
        id=account.id,
        business_name=account.business_name,
        owner_name=account.owner_name,
        owner_email=account.owner_email,
        subscription_tier=account.subscription_tier,
        subscription_status=account.subscription_status,
        is_active=account.is_active,
        trial_ends_at=account.trial_ends_at,
        total_orders=total_orders,
        total_revenue_cents=total_revenue,
        commission_owed_cents=commission,
        created_at=account.created_at
    )


@router.post("/restaurants/{account_id}/suspend")
async def suspend_restaurant(account_id: int, db: Session = Depends(get_db)):
    """
    Suspend a restaurant account.

    Prevents them from receiving new orders/bookings.
    """
    account = db.query(RestaurantAccount).filter(RestaurantAccount.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    account.is_active = False
    account.subscription_status = SubscriptionStatus.SUSPENDED.value
    db.commit()

    logger.warning(f"Restaurant account suspended: {account.id} - {account.business_name}")

    return {
        "status": "success",
        "message": f"Restaurant '{account.business_name}' has been suspended"
    }


@router.post("/restaurants/{account_id}/activate")
async def activate_restaurant(account_id: int, db: Session = Depends(get_db)):
    """
    Reactivate a suspended restaurant account.
    """
    account = db.query(RestaurantAccount).filter(RestaurantAccount.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    account.is_active = True
    if account.subscription_status == SubscriptionStatus.SUSPENDED.value:
        account.subscription_status = SubscriptionStatus.ACTIVE.value
    db.commit()

    logger.info(f"Restaurant account activated: {account.id} - {account.business_name}")

    return {
        "status": "success",
        "message": f"Restaurant '{account.business_name}' has been activated"
    }


@router.get("/analytics/growth")
async def get_growth_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get platform growth analytics.

    Shows trends in restaurant signups, orders, and revenue.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Restaurant signups over time
    signups = db.query(
        func.date(RestaurantAccount.created_at).label('date'),
        func.count(RestaurantAccount.id).label('signups')
    ).filter(
        RestaurantAccount.created_at >= start_date
    ).group_by(
        func.date(RestaurantAccount.created_at)
    ).all()

    # Orders over time
    orders_by_date = db.query(
        func.date(Order.order_date).label('date'),
        func.count(Order.id).label('orders'),
        func.sum(Order.total).label('revenue')
    ).filter(
        Order.order_date >= start_date
    ).group_by(
        func.date(Order.order_date)
    ).all()

    # Bookings over time
    bookings_by_date = db.query(
        func.date(Booking.booking_date).label('date'),
        func.count(Booking.id).label('bookings')
    ).filter(
        Booking.booking_date >= start_date
    ).group_by(
        func.date(Booking.booking_date)
    ).all()

    return {
        "period": {
            "start": start_date,
            "end": end_date,
            "days": days
        },
        "restaurant_signups": [
            {"date": str(s.date), "count": s.signups}
            for s in signups
        ],
        "daily_orders": [
            {"date": str(o.date), "orders": o.orders, "revenue_cents": int(o.revenue or 0)}
            for o in orders_by_date
        ],
        "daily_bookings": [
            {"date": str(b.date), "bookings": b.bookings}
            for b in bookings_by_date
        ]
    }
