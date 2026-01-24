"""
Delivery and order management endpoints.

Handles order creation, delivery tracking, and status updates.
"""

import json
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.database import get_db, SupabaseDB
from backend.schemas_delivery import (
    OrderCreate, OrderUpdate, OrderResponse, OrderWithDelivery,
    DeliveryCreate, DeliveryUpdate, DeliveryResponse
)
from backend.services.sms_service import sms_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new food order."""
    # Get or create customer
    customer = db.query_one("customers", {"phone": order_data.customer_phone})
    if not customer:
        if not order_data.customer_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer name required for new customers"
            )
        customer = db.insert("customers", {
            "phone": order_data.customer_phone,
            "name": order_data.customer_name,
            "email": order_data.customer_email
        })

    # Create order
    order_dict = order_data.model_dump(exclude={'customer_phone', 'customer_name', 'customer_email'})
    order_dict["customer_id"] = customer["id"]
    order_dict["status"] = "confirmed"
    order = db.insert("orders", order_dict)

    # Send SMS confirmation
    try:
        restaurant = db.query_one("restaurants", {"id": order["restaurant_id"]})
        if restaurant and sms_service.enabled:
            # Get restaurant's Twilio phone number
            from_number = None
            if restaurant.get("account_id"):
                account = db.query_one("restaurant_accounts", {"id": restaurant["account_id"]})
                if account:
                    from_number = account.get("twilio_phone_number")

            if from_number:
                # Parse order items for SMS
                try:
                    items = json.loads(order["order_items"]) if isinstance(order["order_items"], str) else order["order_items"]
                    items_text = "\n".join([f"- {item.get('quantity', 1)}x {item.get('name', 'Item')}" for item in items])
                except:
                    items_text = "Your order"

                message = f"""
📦 Order Confirmed!

Restaurant: {restaurant["name"]}
Order #{order["id"]}

{items_text}

Total: ${order["total"] / 100:.2f}
Delivery to: {order["delivery_address"]}

We'll notify you when your order is ready for delivery!
                """.strip()

                sms_service.send_sms(customer["phone"], message, from_number=from_number)
            else:
                logger.warning(f"Cannot send order confirmation SMS - restaurant {restaurant['id']} has no Twilio phone number configured")
    except Exception as e:
        logger.error(f"SMS sending failed: {e}")

    return order


@router.get("/orders/{order_id}", response_model=OrderWithDelivery)
async def get_order(order_id: int, db: SupabaseDB = Depends(get_db)):
    """Get an order by ID with delivery details."""
    order = db.query_one("orders", {"id": order_id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Get associated delivery if exists
    delivery = db.query_one("deliveries", {"order_id": order_id})
    if delivery:
        order["delivery"] = delivery

    return order


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    restaurant_id: Optional[int] = Query(None),
    account_id: Optional[int] = Query(None),
    customer_phone: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: SupabaseDB = Depends(get_db)
):
    """List orders with optional filters. Optimized to query directly by account_id."""
    # Build query - orders table has account_id directly, no need to go through restaurants
    query = db.table("orders").select("*")

    if account_id:
        # Direct query on account_id - uses idx_orders_account_status_created index
        query = query.eq("account_id", account_id)
    elif restaurant_id:
        query = query.eq("restaurant_id", restaurant_id)

    if customer_phone:
        # Look up customer by phone
        customer = db.query_one("customers", {"phone": customer_phone})
        if customer:
            query = query.eq("customer_id", customer["id"])
        else:
            return []  # Customer not found, no orders

    if status_filter:
        query = query.eq("status", status_filter)

    result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
    return result.data or []


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """Update an order status."""
    order = db.query_one("orders", {"id": order_id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    update_dict = order_data.model_dump(exclude_unset=True)
    if update_dict:
        order = db.update("orders", order_id, update_dict)

    # Send status update SMS
    if 'status' in update_dict:
        try:
            customer = db.query_one("customers", {"id": order["customer_id"]})
            restaurant = db.query_one("restaurants", {"id": order["restaurant_id"]})

            if customer and restaurant and sms_service.enabled:
                # Get restaurant's Twilio phone number
                from_number = None
                if restaurant.get("account_id"):
                    account = db.query_one("restaurant_accounts", {"id": restaurant["account_id"]})
                    if account:
                        from_number = account.get("twilio_phone_number")

                if from_number:
                    status_messages = {
                        "preparing": f"🍳 Your order #{order['id']} from {restaurant['name']} is being prepared!",
                        "ready": f"✅ Your order #{order['id']} is ready for pickup/delivery!",
                        "out_for_delivery": f"🚗 Your order #{order['id']} is out for delivery! It should arrive soon.",
                        "delivered": f"🎉 Your order #{order['id']} has been delivered! Enjoy your meal!",
                        "cancelled": f"❌ Your order #{order['id']} has been cancelled."
                    }

                    message = status_messages.get(order["status"], f"Order #{order['id']} status: {order['status']}")
                    sms_service.send_sms(customer["phone"], message, from_number=from_number)
                else:
                    logger.warning(f"Cannot send order status SMS - restaurant {restaurant['id']} has no Twilio phone number configured")
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")

    return order


@router.post("/deliveries", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery(
    delivery_data: DeliveryCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Create a delivery for an order."""
    # Verify order exists
    order = db.query_one("orders", {"id": delivery_data.order_id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Check if delivery already exists
    existing_delivery = db.query_one("deliveries", {"order_id": delivery_data.order_id})
    if existing_delivery:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery already exists for this order"
        )

    # Create delivery
    delivery = db.insert("deliveries", delivery_data.model_dump())

    # Update order status
    db.update("orders", order["id"], {"status": "out_for_delivery"})

    return delivery


@router.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(delivery_id: int, db: SupabaseDB = Depends(get_db)):
    """Get a delivery by ID."""
    delivery = db.query_one("deliveries", {"id": delivery_id})
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )
    return delivery


@router.put("/deliveries/{delivery_id}", response_model=DeliveryResponse)
async def update_delivery(
    delivery_id: int,
    delivery_data: DeliveryUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """Update delivery status and tracking information."""
    delivery = db.query_one("deliveries", {"id": delivery_id})
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    update_dict = delivery_data.model_dump(exclude_unset=True)

    # Update actual delivery time if status is delivered
    if update_dict.get("status") == "delivered" and not delivery.get("actual_delivery_time"):
        update_dict["actual_delivery_time"] = datetime.now().isoformat()

    if update_dict:
        delivery = db.update("deliveries", delivery_id, update_dict)

    # Update order status if delivery is completed
    if delivery.get("status") == "delivered":
        order = db.query_one("orders", {"id": delivery["order_id"]})
        if order:
            db.update("orders", order["id"], {"status": "delivered"})

    return delivery


@router.get("/deliveries", response_model=List[DeliveryResponse])
async def list_deliveries(
    status_filter: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: SupabaseDB = Depends(get_db)
):
    """List deliveries with optional status filter."""
    filters = {}
    if status_filter:
        filters["status"] = status_filter

    deliveries = db.query_all(
        "deliveries",
        filters=filters if filters else None,
        order_by="created_at",
        order_desc=True,
        offset=skip,
        limit=limit
    )
    return deliveries
